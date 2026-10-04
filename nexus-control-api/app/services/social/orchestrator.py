import time
from datetime import timedelta

from app.extensions import db
from app.models import (
    ESTADO_CONECTADO,
    SocialAccount,
    SocialMetricSnapshot,
    SocialPost,
    SocialPostMetric,
    SocialSyncRun,
    _now_utc,
)
from app.services.social import credential_manager, summaries
from app.services.social.config import intervalo_sincronizacion_minutos
from app.services.social.errors import ReauthRequired, SocialProviderError
from app.services.social.fechas import parsear_fecha
from app.services.social.mensajes import NOMBRE_VISIBLE_PLATAFORMA, mensaje_humano
from app.services.social.providers import proveedor_para
from app.services.metricas_sociales import obtener_o_crear


def _actualizar_cuentas(conexion, proveedor, token):
    descubiertas = proveedor.get_accounts(token)

    existentes = {c.id_externo: c for c in conexion.cuentas}
    for datos in descubiertas:
        id_externo = datos.get('id_externo')
        if not id_externo:
            continue
        cuenta = existentes.get(id_externo)
        if cuenta is None:
            cuenta = SocialAccount(
                connection_id=conexion.id,
                plataforma=conexion.plataforma,
                id_externo=id_externo,
                nombre=datos.get('nombre', id_externo),
                seguimiento_activo=True,
            )
            db.session.add(cuenta)
        cuenta.nombre = datos.get('nombre', cuenta.nombre)
        cuenta.usuario = datos.get('usuario')
        cuenta.url_imagen = datos.get('url_imagen')
        cuenta.metadatos_json = datos.get('metadatos') or {}
    db.session.commit()
    return list(conexion.cuentas)


def _registrar_snapshot(conexion, cuenta, nombre_metrica, valor, ahora):
    db.session.add(SocialMetricSnapshot(
        connection_id=conexion.id,
        account_id=cuenta.id,
        plataforma=conexion.plataforma,
        nombre_metrica=nombre_metrica,
        valor=float(valor) if valor is not None else None,
        capturado_at=ahora,
    ))


def _upsert_post(cuenta, datos, ahora):
    post = SocialPost.query.filter_by(
        plataforma=cuenta.plataforma, id_externo_post=datos['id_externo_post'],
    ).first()
    if post is None:
        post = SocialPost(
            account_id=cuenta.id,
            plataforma=cuenta.plataforma,
            id_externo_post=datos['id_externo_post'],
        )
        db.session.add(post)
    post.tipo = datos.get('tipo')
    post.permalink = datos.get('permalink')
    post.extracto = datos.get('extracto')
    fecha_publicacion = parsear_fecha(datos.get('publicado_at'))
    if fecha_publicacion:
        post.publicado_at = fecha_publicacion
    db.session.flush()

    metricas = datos.get('metricas') or {}
    metrica = post.metricas
    if metrica is None:
        metrica = SocialPostMetric(post_id=post.id)
        db.session.add(metrica)
    metrica.me_gusta = metricas.get('me_gusta')
    metrica.comentarios = metricas.get('comentarios')
    metrica.compartidos = metricas.get('compartidos')
    metrica.vistas = metricas.get('vistas')
    metrica.impresiones = metricas.get('impresiones')
    interacciones = sum(v for v in (metricas.get('me_gusta'), metricas.get('comentarios'), metricas.get('compartidos')) if v)
    base_impresiones = metricas.get('impresiones') or metricas.get('vistas')
    metrica.tasa_engagement = round(min((interacciones / base_impresiones) * 100, 100), 2) if base_impresiones else None
    metrica.capturado_at = ahora

    for nombre_metrica in ('me_gusta', 'comentarios', 'compartidos', 'vistas', 'impresiones'):
        valor = metricas.get(nombre_metrica)
        db.session.add(SocialMetricSnapshot(
            post_id=post.id,
            plataforma=cuenta.plataforma,
            nombre_metrica=nombre_metrica,
            valor=float(valor) if valor is not None else None,
            capturado_at=ahora,
        ))
    return post, metricas


def _sincronizar_cuenta(conexion, cuenta, proveedor, token, ahora):
    perfil = proveedor.sync_profile(token, cuenta)
    for nombre_metrica, valor in (perfil or {}).items():
        _registrar_snapshot(conexion, cuenta, nombre_metrica, valor, ahora)

    posts = proveedor.sync_posts(token, cuenta, limite=25)
    totales = {'me_gusta': 0, 'interacciones': 0, 'impresiones': 0}
    for datos_post in posts:
        _, metricas = _upsert_post(cuenta, datos_post, ahora)
        totales['me_gusta'] += metricas.get('me_gusta') or 0
        totales['interacciones'] += sum(
            v for v in (metricas.get('me_gusta'), metricas.get('comentarios'), metricas.get('compartidos')) if v
        )
        totales['impresiones'] += metricas.get('impresiones') or metricas.get('vistas') or 0

    db.session.commit()
    summaries.actualizar_resumen_diario(cuenta, ahora)
    return len(posts) + len(perfil or {}), totales


def _bridge_metrica_legacy(plataforma, totales_acumulados, usuario):
    nombre_visible = NOMBRE_VISIBLE_PLATAFORMA.get(plataforma, plataforma)
    metrica, _ = obtener_o_crear(nombre_visible)
    interacciones = totales_acumulados['interacciones']
    impresiones = totales_acumulados['impresiones']
    metrica.me_gusta = totales_acumulados['me_gusta']
    metrica.interacciones = interacciones
    metrica.impresiones = impresiones
    metrica.engagement = round(min((interacciones / impresiones) * 100, 100), 2) if impresiones else 0.0
    metrica.origen = 'automatico'
    metrica.actualizado_por = usuario or 'sincronizacion_automatica'


def sincronizar_conexion(conexion, disparado_por='programado', usuario=None):
    run = SocialSyncRun(
        connection_id=conexion.id, plataforma=conexion.plataforma,
        disparado_por=disparado_por, usuario=usuario,
    )
    db.session.add(run)
    db.session.commit()

    inicio = time.monotonic()
    try:
        token = credential_manager.obtener_token_vigente(conexion)
        proveedor = proveedor_para(conexion.plataforma)
        cuentas = _actualizar_cuentas(conexion, proveedor, token)

        ahora = _now_utc()
        elementos = 0
        totales_acumulados = {'me_gusta': 0, 'interacciones': 0, 'impresiones': 0}
        for cuenta in cuentas:
            if not cuenta.seguimiento_activo:
                continue
            tocados, totales = _sincronizar_cuenta(conexion, cuenta, proveedor, token, ahora)
            elementos += tocados
            for clave in totales_acumulados:
                totales_acumulados[clave] += totales[clave]

        _bridge_metrica_legacy(conexion.plataforma, totales_acumulados, usuario)

        conexion.estado = ESTADO_CONECTADO
        conexion.ultimo_error = None
        conexion.ultimo_error_detalle = None
        conexion.ultimo_error_tipo = None
        conexion.errores_consecutivos = 0
        conexion.proximo_reintento_at = None
        conexion.ultima_sincronizacion_at = ahora
        conexion.proxima_sincronizacion_at = ahora + timedelta(minutes=intervalo_sincronizacion_minutos())

        run.estado = 'ok'
        run.elementos_actualizados = elementos
        db.session.commit()

    except ReauthRequired as exc:
        run.estado = 'error'
        run.tipo_error = 'permisos_revocados'
        run.error_mensaje = exc.mensaje
        run.error_detalle = exc.detalle
        conexion.proxima_sincronizacion_at = None
        db.session.commit()
    except SocialProviderError as exc:
        if exc.tipo in ('permisos_revocados', 'refresh_expirado'):
            credential_manager.marcar_reauth(conexion, mensaje_humano(exc.tipo, exc.mensaje), exc.detalle)
            conexion.proxima_sincronizacion_at = None
        else:
            credential_manager.marcar_error(conexion, exc)
            conexion.proxima_sincronizacion_at = conexion.proximo_reintento_at
        run.estado = 'error'
        run.tipo_error = exc.tipo
        run.error_mensaje = exc.mensaje
        run.error_detalle = exc.detalle
        db.session.commit()
    except Exception as exc:
        db.session.rollback()
        conexion.errores_consecutivos = (conexion.errores_consecutivos or 0) + 1
        conexion.ultimo_error = 'Ocurrió un error inesperado al sincronizar'
        conexion.ultimo_error_detalle = str(exc)[:2000]
        conexion.ultimo_error_tipo = 'desconocido'
        conexion.proxima_sincronizacion_at = _now_utc() + timedelta(minutes=5)
        run.estado = 'error'
        run.tipo_error = 'desconocido'
        run.error_mensaje = 'Error inesperado'
        run.error_detalle = str(exc)[:2000]
        db.session.commit()
    finally:
        run.finalizado_at = _now_utc()
        run.tiempo_respuesta_ms = int((time.monotonic() - inicio) * 1000)
        db.session.commit()

    return run
