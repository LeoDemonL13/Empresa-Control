from app.services.redes_sociales.comun import ErrorSincronizacion
from app.services.redes_sociales.meta import obtener_metricas_facebook, obtener_metricas_instagram
from app.services.redes_sociales.tiktok import obtener_metricas_tiktok
from app.services.redes_sociales.x import obtener_metricas_x
from app.services.redes_sociales.youtube import obtener_metricas_youtube

CAMPOS_REQUERIDOS = {
    'facebook': ('token_acceso', 'id_pagina'),
    'instagram': ('token_acceso', 'id_cuenta_negocio'),
    'tiktok': ('client_key', 'client_secret', 'token_actualizacion'),
    'youtube': ('clave_api', 'id_canal'),
    'x': ('bearer_token', 'nombre_usuario'),
}

CLIENTES_POR_PLATAFORMA = {
    'facebook': obtener_metricas_facebook,
    'instagram': obtener_metricas_instagram,
    'tiktok': obtener_metricas_tiktok,
    'youtube': obtener_metricas_youtube,
    'x': obtener_metricas_x,
}

PLATAFORMAS_SOPORTADAS = tuple(CAMPOS_REQUERIDOS.keys())

__all__ = [
    'ErrorSincronizacion',
    'CAMPOS_REQUERIDOS',
    'CLIENTES_POR_PLATAFORMA',
    'PLATAFORMAS_SOPORTADAS',
]
