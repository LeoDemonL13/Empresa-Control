import pytest

from app.services.redes_sociales.comun import ErrorSincronizacion
from app.services.redes_sociales.meta import obtener_metricas_facebook, obtener_metricas_instagram
from app.services.redes_sociales.tiktok import URL_TOKEN, obtener_metricas_tiktok
from app.services.redes_sociales.x import obtener_metricas_x
from app.services.redes_sociales.youtube import obtener_metricas_youtube


class _RespuestaFalsa:
    def __init__(self, status_code=200, data=None, texto=''):
        self.status_code = status_code
        self._data = data
        self.text = texto or (str(data) if data is not None else '')

    def json(self):
        if self._data is None:
            raise ValueError('sin cuerpo json')
        return self._data


def test_facebook_mapea_fan_count_impresiones_e_interacciones(monkeypatch):
    def fake_request(metodo, url, **kwargs):
        if url.endswith('/insights'):
            return _RespuestaFalsa(200, {'data': [
                {'name': 'page_impressions', 'period': 'days_28', 'values': [{'value': 5000}, {'value': 5200}]},
                {'name': 'page_post_engagements', 'period': 'days_28', 'values': [{'value': 300}]},
            ]})
        return _RespuestaFalsa(200, {'fan_count': 1200, 'id': '123'})

    monkeypatch.setattr('app.services.redes_sociales.comun.requests.request', fake_request)

    resultado = obtener_metricas_facebook({'token_acceso': 'tok', 'id_pagina': '123'})
    assert resultado == {'me_gusta': 1200, 'interacciones': 300, 'impresiones': 5200, 'engagement': round(300 / 5200 * 100, 2)}


def test_facebook_sin_token_lanza_error_sincronizacion():
    with pytest.raises(ErrorSincronizacion, match='token_acceso'):
        obtener_metricas_facebook({'id_pagina': '123'})


def test_instagram_mapea_total_value(monkeypatch):
    def fake_request(metodo, url, **kwargs):
        if url.endswith('/insights'):
            return _RespuestaFalsa(200, {'data': [
                {'name': 'reach', 'total_value': {'value': 8000}},
                {'name': 'accounts_engaged', 'total_value': {'value': 640}},
            ]})
        return _RespuestaFalsa(200, {'followers_count': 3400})

    monkeypatch.setattr('app.services.redes_sociales.comun.requests.request', fake_request)

    resultado = obtener_metricas_instagram({'token_acceso': 'tok', 'id_cuenta_negocio': '555'})
    assert resultado['me_gusta'] == 3400
    assert resultado['impresiones'] == 8000
    assert resultado['interacciones'] == 640


def test_tiktok_renueva_token_antes_de_pedir_estadisticas(monkeypatch):
    llamadas = []

    def fake_request(metodo, url, **kwargs):
        llamadas.append(url)
        if url == URL_TOKEN:
            return _RespuestaFalsa(200, {'access_token': 'nuevo-token', 'expires_in': 86400})
        assert kwargs['headers']['Authorization'] == 'Bearer nuevo-token'
        return _RespuestaFalsa(200, {'data': {'user': {'follower_count': 500, 'likes_count': 9000, 'video_count': 40}}})

    monkeypatch.setattr('app.services.redes_sociales.comun.requests.request', fake_request)

    resultado = obtener_metricas_tiktok({'client_key': 'ck', 'client_secret': 'cs', 'token_actualizacion': 'rt'})
    assert resultado['me_gusta'] == 9000
    assert resultado['impresiones'] == 0
    assert resultado['interacciones'] == 0
    assert llamadas[0] == URL_TOKEN


def test_tiktok_sin_access_token_en_respuesta_lanza_error(monkeypatch):
    monkeypatch.setattr(
        'app.services.redes_sociales.comun.requests.request',
        lambda metodo, url, **kwargs: _RespuestaFalsa(200, {'expires_in': 86400}),
    )
    with pytest.raises(ErrorSincronizacion, match='token de acceso'):
        obtener_metricas_tiktok({'client_key': 'ck', 'client_secret': 'cs', 'token_actualizacion': 'rt'})


def test_youtube_suma_estadisticas_de_videos_recientes(monkeypatch):
    def fake_request(metodo, url, **kwargs):
        if url.endswith('/search'):
            return _RespuestaFalsa(200, {'items': [{'id': {'videoId': 'v1'}}, {'id': {'videoId': 'v2'}}]})
        return _RespuestaFalsa(200, {'items': [
            {'statistics': {'viewCount': '1000', 'likeCount': '100', 'commentCount': '10'}},
            {'statistics': {'viewCount': '2000', 'likeCount': '150', 'commentCount': '20'}},
        ]})

    monkeypatch.setattr('app.services.redes_sociales.comun.requests.request', fake_request)

    resultado = obtener_metricas_youtube({'clave_api': 'k', 'id_canal': 'c1'})
    assert resultado['me_gusta'] == 250
    assert resultado['interacciones'] == 280
    assert resultado['impresiones'] == 3000


def test_youtube_sin_videos_devuelve_ceros(monkeypatch):
    monkeypatch.setattr(
        'app.services.redes_sociales.comun.requests.request',
        lambda metodo, url, **kwargs: _RespuestaFalsa(200, {'items': []}),
    )
    resultado = obtener_metricas_youtube({'clave_api': 'k', 'id_canal': 'c1'})
    assert resultado == {'me_gusta': 0, 'interacciones': 0, 'impresiones': 0, 'engagement': 0.0}


def test_x_resuelve_usuario_y_suma_publicaciones_recientes(monkeypatch):
    def fake_request(metodo, url, **kwargs):
        if '/by/username/' in url:
            return _RespuestaFalsa(200, {'data': {'id': '999', 'username': 'empresa'}})
        return _RespuestaFalsa(200, {'data': [
            {'public_metrics': {'like_count': 10, 'retweet_count': 2, 'reply_count': 1, 'quote_count': 0, 'impression_count': 500}},
            {'public_metrics': {'like_count': 20, 'retweet_count': 3, 'reply_count': 2, 'quote_count': 1, 'impression_count': 800}},
        ]})

    monkeypatch.setattr('app.services.redes_sociales.comun.requests.request', fake_request)

    resultado = obtener_metricas_x({'bearer_token': 'tok', 'nombre_usuario': '@empresa'})
    assert resultado['me_gusta'] == 30
    assert resultado['interacciones'] == 30 + 9
    assert resultado['impresiones'] == 1300


def test_x_usuario_inexistente_lanza_error(monkeypatch):
    monkeypatch.setattr(
        'app.services.redes_sociales.comun.requests.request',
        lambda metodo, url, **kwargs: _RespuestaFalsa(200, {'data': None}),
    )
    with pytest.raises(ErrorSincronizacion, match='No se encontró'):
        obtener_metricas_x({'bearer_token': 'tok', 'nombre_usuario': 'empresa'})


def test_respuesta_http_de_error_incluye_mensaje_de_la_plataforma(monkeypatch):
    monkeypatch.setattr(
        'app.services.redes_sociales.comun.requests.request',
        lambda metodo, url, **kwargs: _RespuestaFalsa(401, {'error': {'message': 'token inválido'}}),
    )
    with pytest.raises(ErrorSincronizacion, match='token inválido'):
        obtener_metricas_facebook({'token_acceso': 'malo', 'id_pagina': '1'})


def test_respuesta_sin_json_valido_lanza_error_sincronizacion(monkeypatch):
    monkeypatch.setattr(
        'app.services.redes_sociales.comun.requests.request',
        lambda metodo, url, **kwargs: _RespuestaFalsa(200, None, texto='<html>no es json</html>'),
    )
    with pytest.raises(ErrorSincronizacion, match='sin JSON'):
        obtener_metricas_facebook({'token_acceso': 'tok', 'id_pagina': '1'})


def test_fallo_de_red_lanza_error_sincronizacion(monkeypatch):
    import requests

    def fake_request(metodo, url, **kwargs):
        raise requests.ConnectionError('sin conexión')

    monkeypatch.setattr('app.services.redes_sociales.comun.requests.request', fake_request)
    with pytest.raises(ErrorSincronizacion, match='No se pudo contactar'):
        obtener_metricas_facebook({'token_acceso': 'tok', 'id_pagina': '1'})
