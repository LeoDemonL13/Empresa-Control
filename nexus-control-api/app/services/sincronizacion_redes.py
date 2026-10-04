from datetime import datetime, timezone

from app.constants import ROLE_ADMIN, ROLE_SUPER_ADMIN
from app.extensions import db
from app.models import ConexionRedSocial
from app.realtime import emit_to_role
from app.services.metricas_sociales import obtener_o_crear
from app.services.redes_sociales import CLIENTES_POR_PLATAFORMA, ErrorSincronizacion

NOMBRE_VISIBLE_PLATAFORMA = {
    'facebook': 'Facebook',
    'instagram': 'Instagram',
    'tiktok': 'TikTok',
    'youtube': 'YouTube',
    'x': 'X',
}

ACTUALIZADO_POR_SINCRONIZACION = 'sincronizacion_automatica'


def sincronizar_plataforma(plataforma):
    conexion = ConexionRedSocial.query.filter_by(plataforma=plataforma).first()
    if not conexion or not conexion.credenciales_cifradas:
        return False, 'No hay credenciales guardadas para esta plataforma'

    cliente = CLIENTES_POR_PLATAFORMA.get(plataforma)
    if not cliente:
        return False, f'Plataforma no soportada: {plataforma}'

    ahora = datetime.now(timezone.utc)
    conexion.ultima_sincronizacion = ahora

    try:
        resultado = cliente(conexion.credenciales_cifradas)
    except ErrorSincronizacion as exc:
        conexion.ultimo_error = str(exc)[:2000]
        db.session.commit()
        emit_to_role((ROLE_SUPER_ADMIN, ROLE_ADMIN), 'conexion_social:actualizada', {'plataforma': plataforma})
        return False, str(exc)
    except Exception as exc:
        conexion.ultimo_error = f'Error inesperado: {exc}'[:2000]
        db.session.commit()
        emit_to_role((ROLE_SUPER_ADMIN, ROLE_ADMIN), 'conexion_social:actualizada', {'plataforma': plataforma})
        return False, str(exc)

    nombre_visible = NOMBRE_VISIBLE_PLATAFORMA.get(plataforma, plataforma)
    metrica, _ = obtener_o_crear(nombre_visible)
    metrica.me_gusta = resultado['me_gusta']
    metrica.interacciones = resultado['interacciones']
    metrica.impresiones = resultado['impresiones']
    metrica.engagement = resultado['engagement']
    metrica.origen = 'automatico'
    metrica.actualizado_por = ACTUALIZADO_POR_SINCRONIZACION

    conexion.ultimo_error = None

    db.session.commit()
    emit_to_role((ROLE_SUPER_ADMIN, ROLE_ADMIN), 'metrica:actualizada', {'id': metrica.id})
    emit_to_role((ROLE_SUPER_ADMIN, ROLE_ADMIN), 'conexion_social:actualizada', {'plataforma': plataforma})
    return True, None


def sincronizar_todas():
    resultados = {}
    for conexion in ConexionRedSocial.query.all():
        ok, error = sincronizar_plataforma(conexion.plataforma)
        resultados[conexion.plataforma] = {'ok': ok, 'error': error}
    return resultados
