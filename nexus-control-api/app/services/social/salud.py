from datetime import timedelta

from app.models import ESTADO_CONECTADO, PLATAFORMAS_SOCIALES, SocialConnection, SocialSyncRun, _now_utc
from app.services.social.config import intervalo_sincronizacion_minutos, plataforma_configurada
from app.services.social.fechas import asegurar_utc

ICONO_POR_ESTADO = {
    'CONNECTED': '🟢',
    'REFRESHING': '🔵',
    'TOKEN_EXPIRING': '🟠',
    'REAUTH_REQUIRED': '🔴',
    'ERROR': '🔴',
    'DISCONNECTED': '⚫',
}

TEXTO_POR_ESTADO = {
    'CONNECTED': 'Conectado',
    'REFRESHING': 'Renovando sesión',
    'TOKEN_EXPIRING': 'La sesión está por expirar',
    'REAUTH_REQUIRED': 'Requiere reconexión',
    'ERROR': 'Error de sincronización',
    'DISCONNECTED': 'No conectado',
}


def estado_visible(conexion):
    estado = conexion.estado
    expira_at = asegurar_utc(conexion.expira_at)
    if estado == ESTADO_CONECTADO and expira_at and expira_at <= _now_utc() + timedelta(hours=1):
        return 'TOKEN_EXPIRING'
    return estado


def conexion_vacia(plataforma):
    return {
        'plataforma': plataforma,
        'conectada': False,
        'estado': 'DISCONNECTED',
        'icono': ICONO_POR_ESTADO['DISCONNECTED'],
        'estado_texto': TEXTO_POR_ESTADO['DISCONNECTED'],
        'configurada': plataforma_configurada(plataforma),
        'cuenta_externa': None,
        'cuentas': [],
        'ultima_sincronizacion': None,
        'proxima_sincronizacion': None,
        'ultimo_error': None,
        'errores_consecutivos': 0,
        'conectado_por': None,
        'conectado_at': None,
    }


def resumen_conexion(conexion: SocialConnection):
    estado = estado_visible(conexion)
    cuentas = [
        {
            'id': c.id,
            'id_externo': c.id_externo,
            'nombre': c.nombre,
            'usuario': c.usuario,
            'url_imagen': c.url_imagen,
            'seguimiento_activo': c.seguimiento_activo,
        }
        for c in conexion.cuentas
    ]
    return {
        'plataforma': conexion.plataforma,
        'conectada': conexion.conectada(),
        'estado': estado,
        'icono': ICONO_POR_ESTADO.get(estado, '⚫'),
        'estado_texto': TEXTO_POR_ESTADO.get(estado, estado),
        'configurada': plataforma_configurada(conexion.plataforma),
        'cuenta_externa': conexion.etiqueta_externa,
        'cuentas': cuentas,
        'ultima_sincronizacion': conexion.ultima_sincronizacion_at.isoformat() if conexion.ultima_sincronizacion_at else None,
        'proxima_sincronizacion': conexion.proxima_sincronizacion_at.isoformat() if conexion.proxima_sincronizacion_at else None,
        'ultimo_error': conexion.ultimo_error,
        'errores_consecutivos': conexion.errores_consecutivos,
        'conectado_por': conexion.conectado_por,
        'conectado_at': conexion.conectado_at.isoformat() if conexion.conectado_at else None,
    }


def panel_administracion(conexion: SocialConnection):
    base = resumen_conexion(conexion)
    runs = (
        SocialSyncRun.query.filter_by(connection_id=conexion.id)
        .order_by(SocialSyncRun.iniciado_at.desc()).limit(10).all()
    )
    base['alcance'] = conexion.alcance
    base['errores_recientes'] = [
        {
            'iniciado_at': r.iniciado_at.isoformat(),
            'finalizado_at': r.finalizado_at.isoformat() if r.finalizado_at else None,
            'estado': r.estado,
            'tipo_error': r.tipo_error,
            'mensaje': r.error_mensaje,
            'disparado_por': r.disparado_por,
        }
        for r in runs
    ]
    return base


def estado_sistema():
    conexiones = {c.plataforma: c for c in SocialConnection.query.all()}
    plataformas = []
    for plataforma in PLATAFORMAS_SOCIALES:
        conexion = conexiones.get(plataforma)
        ultima_run = (
            SocialSyncRun.query.filter_by(plataforma=plataforma)
            .order_by(SocialSyncRun.iniciado_at.desc()).first()
        )
        plataformas.append({
            'plataforma': plataforma,
            'conectada': conexion.conectada() if conexion else False,
            'estado': estado_visible(conexion) if conexion else 'DISCONNECTED',
            'ultima_sincronizacion': (
                conexion.ultima_sincronizacion_at.isoformat()
                if conexion and conexion.ultima_sincronizacion_at else None
            ),
            'proxima_sincronizacion': (
                conexion.proxima_sincronizacion_at.isoformat()
                if conexion and conexion.proxima_sincronizacion_at else None
            ),
            'ultimo_tiempo_respuesta_ms': ultima_run.tiempo_respuesta_ms if ultima_run else None,
            'ultimos_elementos_actualizados': ultima_run.elementos_actualizados if ultima_run else None,
            'ultimo_resultado': ultima_run.estado if ultima_run else None,
        })
    return {
        'intervalo_minutos': intervalo_sincronizacion_minutos(),
        'plataformas': plataformas,
    }
