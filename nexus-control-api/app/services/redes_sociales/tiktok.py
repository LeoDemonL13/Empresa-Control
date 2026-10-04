from app.services.redes_sociales.comun import (
    ErrorSincronizacion,
    campo_requerido,
    metricas_resultado,
    solicitar_json,
)

URL_TOKEN = 'https://open.tiktokapis.com/v2/oauth/token/'
URL_INFO_USUARIO = 'https://open.tiktokapis.com/v2/user/info/'


def _renovar_token_acceso(client_key, client_secret, token_actualizacion):
    cuerpo = solicitar_json(
        'POST', URL_TOKEN,
        headers={'Content-Type': 'application/x-www-form-urlencoded'},
        data={
            'client_key': client_key,
            'client_secret': client_secret,
            'grant_type': 'refresh_token',
            'refresh_token': token_actualizacion,
        },
    )
    token_acceso = cuerpo.get('access_token')
    if not token_acceso:
        raise ErrorSincronizacion('TikTok no devolvió un token de acceso válido')
    return token_acceso


def obtener_metricas_tiktok(credenciales):
    client_key = campo_requerido(credenciales, 'client_key')
    client_secret = campo_requerido(credenciales, 'client_secret')
    token_actualizacion = campo_requerido(credenciales, 'token_actualizacion')

    token_acceso = _renovar_token_acceso(client_key, client_secret, token_actualizacion)

    cuerpo = solicitar_json(
        'GET', URL_INFO_USUARIO,
        params={'fields': 'follower_count,likes_count,video_count'},
        headers={'Authorization': f'Bearer {token_acceso}'},
    )
    datos = (cuerpo.get('data') or {}).get('user') or {}

    return metricas_resultado(
        me_gusta=datos.get('likes_count', 0),
        interacciones=0,
        impresiones=0,
    )
