from datetime import timedelta

from app.extensions import db
from app.models import (
    ESTADO_CONECTADO,
    ESTADO_DESCONECTADO,
    ESTADO_ERROR,
    ESTADO_REAUTH_REQUERIDA,
    ESTADO_REFRESCANDO,
    _now_utc,
)
from app.services.social.errors import ReauthRequired, SocialProviderError
from app.services.social.fechas import asegurar_utc
from app.services.social.mensajes import mensaje_humano
from app.services.social.providers import proveedor_para

MARGEN_RENOVACION = timedelta(minutes=5)
BACKOFF_MINUTOS = (1, 2, 5, 15, 30)


def guardar_tokens(conexion, datos, conectado_por=None):
    ahora = _now_utc()
    conexion.access_token_cifrado = datos['access_token']
    if datos.get('refresh_token'):
        conexion.refresh_token_cifrado = datos['refresh_token']
    conexion.tipo_token = datos.get('token_type')
    if datos.get('scope'):
        conexion.alcance = datos['scope']
    conexion.expira_at = ahora + timedelta(seconds=int(datos['expires_in'])) if datos.get('expires_in') else None
    if datos.get('refresh_expires_in'):
        conexion.refresh_expira_at = ahora + timedelta(seconds=int(datos['refresh_expires_in']))
    if datos.get('external_user_id'):
        conexion.id_externo_usuario = datos['external_user_id']
    if datos.get('external_user_label'):
        conexion.etiqueta_externa = datos['external_user_label']
    conexion.estado = ESTADO_CONECTADO
    conexion.ultimo_error = None
    conexion.ultimo_error_detalle = None
    conexion.ultimo_error_tipo = None
    conexion.errores_consecutivos = 0
    conexion.proximo_reintento_at = None
    if conectado_por:
        conexion.conectado_por = conectado_por
        conexion.conectado_at = ahora
    db.session.commit()


def marcar_reauth(conexion, mensaje, detalle=None):
    conexion.estado = ESTADO_REAUTH_REQUERIDA
    conexion.ultimo_error = mensaje
    conexion.ultimo_error_detalle = detalle
    conexion.ultimo_error_tipo = 'permisos_revocados'
    db.session.commit()


def marcar_error(conexion, exc: SocialProviderError):
    conexion.errores_consecutivos = (conexion.errores_consecutivos or 0) + 1
    indice = min(conexion.errores_consecutivos - 1, len(BACKOFF_MINUTOS) - 1)
    minutos = BACKOFF_MINUTOS[indice]
    if exc.retry_after:
        minutos = max(minutos, exc.retry_after / 60)
    conexion.proximo_reintento_at = _now_utc() + timedelta(minutes=minutos)
    conexion.ultimo_error = mensaje_humano(exc.tipo, exc.mensaje)
    conexion.ultimo_error_detalle = exc.detalle
    conexion.ultimo_error_tipo = exc.tipo
    if conexion.estado not in (ESTADO_REAUTH_REQUERIDA, ESTADO_DESCONECTADO):
        conexion.estado = ESTADO_ERROR
    db.session.commit()


def obtener_token_vigente(conexion):
    ahora = _now_utc()
    expira_at = asegurar_utc(conexion.expira_at)
    necesita_refresh = expira_at is not None and expira_at <= ahora + MARGEN_RENOVACION

    if not necesita_refresh:
        if not conexion.access_token_cifrado:
            raise ReauthRequired('No hay credenciales guardadas para esta plataforma')
        return conexion.access_token_cifrado

    if not conexion.refresh_token_cifrado:
        marcar_reauth(conexion, 'El token de acceso expiró y no hay refresh token guardado')
        raise ReauthRequired('Token expirado sin refresh token')

    refresh_expira_at = asegurar_utc(conexion.refresh_expira_at)
    if refresh_expira_at and refresh_expira_at <= ahora:
        marcar_reauth(conexion, 'El refresh token expiró; hay que reconectar esta plataforma')
        raise ReauthRequired('Refresh token expirado')

    conexion.estado = ESTADO_REFRESCANDO
    db.session.commit()

    proveedor = proveedor_para(conexion.plataforma)
    try:
        datos = proveedor.refresh_token(conexion.refresh_token_cifrado)
    except SocialProviderError as exc:
        if exc.tipo in ('refresh_expirado', 'permisos_revocados'):
            marcar_reauth(conexion, mensaje_humano(exc.tipo, exc.mensaje), exc.detalle)
            raise ReauthRequired(mensaje_humano(exc.tipo, exc.mensaje), exc.detalle) from exc
        marcar_error(conexion, exc)
        raise

    guardar_tokens(conexion, datos)
    return conexion.access_token_cifrado
