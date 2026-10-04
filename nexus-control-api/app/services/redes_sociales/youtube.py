from app.services.redes_sociales.comun import campo_requerido, metricas_resultado, solicitar_json

URL_BASE = 'https://www.googleapis.com/youtube/v3'
MAXIMO_VIDEOS_RECIENTES = 10


def _ids_videos_recientes(id_canal, clave_api):
    cuerpo = solicitar_json(
        'GET', f'{URL_BASE}/search',
        params={
            'part': 'id',
            'channelId': id_canal,
            'order': 'date',
            'maxResults': MAXIMO_VIDEOS_RECIENTES,
            'type': 'video',
            'key': clave_api,
        },
    )
    return [
        item['id']['videoId']
        for item in cuerpo.get('items', [])
        if item.get('id', {}).get('videoId')
    ]


def _estadisticas_videos(ids_videos, clave_api):
    if not ids_videos:
        return []
    cuerpo = solicitar_json(
        'GET', f'{URL_BASE}/videos',
        params={'part': 'statistics', 'id': ','.join(ids_videos), 'key': clave_api},
    )
    return [item.get('statistics', {}) for item in cuerpo.get('items', [])]


def obtener_metricas_youtube(credenciales):
    clave_api = campo_requerido(credenciales, 'clave_api')
    id_canal = campo_requerido(credenciales, 'id_canal')

    ids_videos = _ids_videos_recientes(id_canal, clave_api)
    estadisticas = _estadisticas_videos(ids_videos, clave_api)

    total_me_gusta = sum(int(e.get('likeCount', 0) or 0) for e in estadisticas)
    total_comentarios = sum(int(e.get('commentCount', 0) or 0) for e in estadisticas)
    total_vistas = sum(int(e.get('viewCount', 0) or 0) for e in estadisticas)

    return metricas_resultado(
        me_gusta=total_me_gusta,
        interacciones=total_me_gusta + total_comentarios,
        impresiones=total_vistas,
    )
