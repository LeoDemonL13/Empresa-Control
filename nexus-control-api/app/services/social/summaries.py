from datetime import datetime, time, timedelta, timezone

from app.extensions import db
from app.models import (
    SocialAccount,
    SocialDailySummary,
    SocialMetricSnapshot,
    SocialPost,
    SocialPostMetric,
    _now_utc,
)
from app.services.social.mensajes import NOMBRE_VISIBLE_PLATAFORMA


def _inicio_dia_utc(fecha):
    return datetime.combine(fecha, time.min, tzinfo=timezone.utc)


def _fin_dia_utc(fecha):
    return _inicio_dia_utc(fecha) + timedelta(days=1)


def _ultimo_valor_metrica(account_id, nombre_metrica, limite=None):
    consulta = SocialMetricSnapshot.query.filter_by(account_id=account_id, nombre_metrica=nombre_metrica)
    if limite is not None:
        consulta = consulta.filter(SocialMetricSnapshot.capturado_at <= limite)
    fila = consulta.order_by(SocialMetricSnapshot.capturado_at.desc()).first()
    return fila.valor if fila else None


def actualizar_resumen_diario(cuenta: SocialAccount, ahora):
    fecha = ahora.date()
    inicio = _inicio_dia_utc(fecha)
    fin = _fin_dia_utc(fecha)

    posts_hoy = SocialPost.query.filter(
        SocialPost.account_id == cuenta.id,
        SocialPost.publicado_at >= inicio,
        SocialPost.publicado_at < fin,
    ).all()

    total_me_gusta = total_comentarios = total_compartidos = total_vistas = 0
    tasas = []
    mejor_post = None
    peor_post = None
    for post in posts_hoy:
        m = post.metricas
        if m is None:
            continue
        total_me_gusta += m.me_gusta or 0
        total_comentarios += m.comentarios or 0
        total_compartidos += m.compartidos or 0
        total_vistas += m.vistas or 0
        if m.tasa_engagement is not None:
            tasas.append(m.tasa_engagement)
            if mejor_post is None or m.tasa_engagement > (mejor_post.metricas.tasa_engagement or -1):
                mejor_post = post
            if peor_post is None or m.tasa_engagement < (peor_post.metricas.tasa_engagement or 101):
                peor_post = post

    fila = SocialDailySummary.query.filter_by(account_id=cuenta.id, fecha=fecha).first()
    if fila is None:
        fila = SocialDailySummary(account_id=cuenta.id, plataforma=cuenta.plataforma, fecha=fecha)
        db.session.add(fila)

    anterior = SocialDailySummary.query.filter_by(
        account_id=cuenta.id, fecha=fecha - timedelta(days=1),
    ).first()

    fila.seguidores_fin = _ultimo_valor_metrica(cuenta.id, 'seguidores')
    fila.cambio_seguidores = (
        int(fila.seguidores_fin - anterior.seguidores_fin)
        if fila.seguidores_fin is not None and anterior is not None and anterior.seguidores_fin is not None
        else None
    )
    fila.publicaciones_nuevas = len(posts_hoy)
    fila.total_me_gusta = total_me_gusta
    fila.total_comentarios = total_comentarios
    fila.total_compartidos = total_compartidos
    fila.total_vistas = total_vistas
    fila.tasa_engagement_promedio = round(sum(tasas) / len(tasas), 2) if tasas else None
    fila.mejor_post_id = mejor_post.id if mejor_post else None
    fila.peor_post_id = peor_post.id if peor_post else None
    db.session.commit()
    return fila


def _formatear_numero(valor):
    if valor is None:
        return 'No disponible'
    return f'{valor:,.0f}' if isinstance(valor, float) else f'{valor:,}'


def _generar_narrativa(plataforma, dias, publicaciones, interacciones, tasa_promedio, seguidores_inicio, seguidores_fin):
    nombre = NOMBRE_VISIBLE_PLATAFORMA.get(plataforma, plataforma) if plataforma else 'Todas las redes'
    partes = [f'En los últimos {dias} día(s), {nombre} registró {publicaciones} publicación(es)']
    if interacciones is not None:
        partes.append(f'con {_formatear_numero(interacciones)} interacciones en total')
    if tasa_promedio is not None:
        partes.append(f'y una tasa de engagement promedio de {tasa_promedio:.2f}%')
    frase = ' '.join(partes) + '.'

    if seguidores_inicio is not None and seguidores_fin is not None:
        cambio = seguidores_fin - seguidores_inicio
        signo = '+' if cambio >= 0 else ''
        frase += (
            f' Los seguidores pasaron de {_formatear_numero(seguidores_inicio)} a '
            f'{_formatear_numero(seguidores_fin)} ({signo}{cambio:,}).'
        )
    else:
        frase += ' El dato de seguidores no está disponible para este periodo.'
    return frase


def _resumen_post(post):
    if post is None:
        return None
    m = post.metricas
    return {
        'id_externo_post': post.id_externo_post,
        'permalink': post.permalink,
        'extracto': post.extracto,
        'publicado_at': post.publicado_at.isoformat() if post.publicado_at else None,
        'tasa_engagement': m.tasa_engagement if m else None,
        'me_gusta': m.me_gusta if m else None,
    }


def obtener_resumen(desde, hasta, plataforma=None):
    consulta = SocialAccount.query
    if plataforma:
        consulta = consulta.filter(SocialAccount.plataforma == plataforma)
    cuentas = consulta.all()

    dias = max((hasta - desde).total_seconds() / 86400, 1 / 24)
    publicaciones_total = 0
    interacciones_total = 0
    impresiones_total = 0
    tasas = []
    seguidores_inicio_total = 0
    seguidores_fin_total = 0
    hay_seguidores_inicio = False
    hay_seguidores_fin = False
    mejor_global = None
    peor_global = None
    por_cuenta = []

    for cuenta in cuentas:
        posts = SocialPost.query.filter(
            SocialPost.account_id == cuenta.id,
            SocialPost.publicado_at >= desde,
            SocialPost.publicado_at < hasta,
        ).all()
        me_gusta = comentarios = compartidos = impresiones = 0
        tasas_cuenta = []
        mejor = None
        peor = None
        for post in posts:
            m = post.metricas
            if m is None:
                continue
            me_gusta += m.me_gusta or 0
            comentarios += m.comentarios or 0
            compartidos += m.compartidos or 0
            impresiones += m.impresiones or m.vistas or 0
            if m.tasa_engagement is not None:
                tasas_cuenta.append(m.tasa_engagement)
                if mejor is None or m.tasa_engagement > (mejor.metricas.tasa_engagement or -1):
                    mejor = post
                if peor is None or m.tasa_engagement < (peor.metricas.tasa_engagement or 101):
                    peor = post

        seguidores_inicio = _ultimo_valor_metrica(cuenta.id, 'seguidores', desde)
        seguidores_fin = _ultimo_valor_metrica(cuenta.id, 'seguidores', hasta)

        publicaciones_total += len(posts)
        interacciones_total += me_gusta + comentarios + compartidos
        impresiones_total += impresiones
        tasas.extend(tasas_cuenta)
        if seguidores_inicio is not None:
            seguidores_inicio_total += seguidores_inicio
            hay_seguidores_inicio = True
        if seguidores_fin is not None:
            seguidores_fin_total += seguidores_fin
            hay_seguidores_fin = True
        if mejor and (mejor_global is None or (mejor.metricas.tasa_engagement or -1) > (mejor_global.metricas.tasa_engagement or -1)):
            mejor_global = mejor
        if peor and (peor_global is None or (peor.metricas.tasa_engagement or 101) < (peor_global.metricas.tasa_engagement or 101)):
            peor_global = peor

        por_cuenta.append({
            'plataforma': cuenta.plataforma,
            'cuenta': cuenta.nombre,
            'publicaciones': len(posts),
            'me_gusta': me_gusta,
            'comentarios': comentarios,
            'compartidos': compartidos,
            'impresiones': impresiones or None,
            'tasa_engagement_promedio': round(sum(tasas_cuenta) / len(tasas_cuenta), 2) if tasas_cuenta else None,
            'seguidores_inicio': seguidores_inicio,
            'seguidores_fin': seguidores_fin,
        })

    tasa_promedio = round(sum(tasas) / len(tasas), 2) if tasas else None
    narrativa = _generar_narrativa(
        plataforma, round(dias, 1), publicaciones_total,
        interacciones_total if (interacciones_total or publicaciones_total) else None,
        tasa_promedio,
        seguidores_inicio_total if hay_seguidores_inicio else None,
        seguidores_fin_total if hay_seguidores_fin else None,
    )

    return {
        'desde': desde.isoformat(),
        'hasta': hasta.isoformat(),
        'plataforma': plataforma,
        'publicaciones': publicaciones_total,
        'interacciones': interacciones_total,
        'impresiones': impresiones_total or None,
        'tasa_engagement_promedio': tasa_promedio,
        'seguidores_inicio': seguidores_inicio_total if hay_seguidores_inicio else None,
        'seguidores_fin': seguidores_fin_total if hay_seguidores_fin else None,
        'mejor_publicacion': _resumen_post(mejor_global),
        'peor_publicacion': _resumen_post(peor_global),
        'por_cuenta': por_cuenta,
        'narrativa': narrativa,
    }


def rango_predefinido(nombre):
    ahora = _now_utc()
    if nombre == '24h':
        return ahora - timedelta(hours=24), ahora
    if nombre == '7d':
        return ahora - timedelta(days=7), ahora
    if nombre == '30d':
        return ahora - timedelta(days=30), ahora
    return None
