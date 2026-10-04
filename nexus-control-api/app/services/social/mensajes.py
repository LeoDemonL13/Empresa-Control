MENSAJES_POR_TIPO_ERROR = {
    'temporal': 'Hubo un problema temporal al sincronizar; se reintentará automáticamente.',
    'timeout': 'La plataforma tardó demasiado en responder; se reintentará automáticamente.',
    'limite_tasa': 'Se alcanzó el límite de solicitudes de la plataforma; se reintentará automáticamente.',
    'servidor_caido': 'La plataforma no está respondiendo en este momento; se reintentará automáticamente.',
    'token_expirado': 'La sesión con la plataforma expiró; el sistema intentará renovarla automáticamente.',
    'refresh_expirado': 'La autorización expiró por completo; es necesario volver a conectar esta plataforma.',
    'permisos_revocados': 'Los permisos otorgados fueron revocados o cambiaron; es necesario volver a conectar esta plataforma.',
    'cuenta_eliminada': 'La cuenta o página conectada ya no existe en la plataforma.',
    'api_deshabilitada': 'La plataforma deshabilitó el acceso a esta función para la aplicación.',
    'desconocido': 'Ocurrió un error inesperado al sincronizar con la plataforma.',
}

NOMBRE_VISIBLE_PLATAFORMA = {
    'facebook': 'Facebook',
    'instagram': 'Instagram',
    'tiktok': 'TikTok',
    'youtube': 'YouTube',
}


def mensaje_humano(tipo_error, mensaje_original=None):
    return MENSAJES_POR_TIPO_ERROR.get(tipo_error, mensaje_original or MENSAJES_POR_TIPO_ERROR['desconocido'])
