from app.services.redes_sociales.comun import (
    ErrorSincronizacion,
    campo_requerido,
    metricas_resultado,
    solicitar_json,
)

URL_BASE = 'https://api.twitter.com/2'
MAXIMO_PUBLICACIONES_RECIENTES = 10


def _id_usuario(nombre_usuario, bearer_token):
    cuerpo = solicitar_json(
        'GET', f'{URL_BASE}/users/by/username/{nombre_usuario}',
        headers={'Authorization': f'Bearer {bearer_token}'},
    )
    datos = cuerpo.get('data') or {}
    id_usuario = datos.get('id')
    if not id_usuario:
        raise ErrorSincronizacion(f'No se encontró la cuenta "{nombre_usuario}" en X')
    return id_usuario


def _publicaciones_recientes(id_usuario, bearer_token):
    cuerpo = solicitar_json(
        'GET', f'{URL_BASE}/users/{id_usuario}/tweets',
        params={'max_results': MAXIMO_PUBLICACIONES_RECIENTES, 'tweet.fields': 'public_metrics'},
        headers={'Authorization': f'Bearer {bearer_token}'},
    )
    return [item.get('public_metrics', {}) for item in cuerpo.get('data', [])]


def obtener_metricas_x(credenciales):
    bearer_token = campo_requerido(credenciales, 'bearer_token')
    nombre_usuario = campo_requerido(credenciales, 'nombre_usuario').lstrip('@')

    id_usuario = _id_usuario(nombre_usuario, bearer_token)
    publicaciones = _publicaciones_recientes(id_usuario, bearer_token)

    total_me_gusta = sum(int(p.get('like_count', 0) or 0) for p in publicaciones)
    total_otras_interacciones = sum(
        int(p.get('retweet_count', 0) or 0) + int(p.get('reply_count', 0) or 0) + int(p.get('quote_count', 0) or 0)
        for p in publicaciones
    )
    total_impresiones = sum(int(p.get('impression_count', 0) or 0) for p in publicaciones)

    return metricas_resultado(
        me_gusta=total_me_gusta,
        interacciones=total_me_gusta + total_otras_interacciones,
        impresiones=total_impresiones,
    )
