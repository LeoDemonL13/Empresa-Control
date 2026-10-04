import pytest

from app.services.social.errors import SocialProviderError
from app.services.social.providers.meta import MetaAdapter, _clasificar_meta
from app.services.social.providers.tiktok import TikTokAdapter, _clasificar_tiktok
from app.services.social.providers.youtube import YouTubeAdapter, _clasificar_google


def _secuencia(respuestas):
    iterador = iter(respuestas)

    def _fake(metodo, url, **kwargs):
        resultado = next(iterador)
        if isinstance(resultado, Exception):
            raise resultado
        return resultado

    return _fake


def test_meta_authorize_url_facebook_usa_scope_de_paginas():
    adaptador = MetaAdapter('facebook')
    url = adaptador.build_authorize_url('estado-x', 'http://localhost/callback')
    assert 'pages_show_list' in url
    assert 'state=estado-x' in url
    assert 'response_type=code' in url


def test_meta_authorize_url_instagram_usa_scope_de_instagram():
    adaptador = MetaAdapter('instagram')
    url = adaptador.build_authorize_url('estado-x', 'http://localhost/callback')
    assert 'instagram_basic' in url


def test_meta_exchange_code_devuelve_token_largo_y_perfil(monkeypatch):
    adaptador = MetaAdapter('facebook')
    monkeypatch.setattr(
        'app.services.social.providers.meta.solicitar',
        _secuencia([
            {'access_token': 'corto', 'expires_in': 3600},
            {'access_token': 'largo-duracion', 'expires_in': 5184000, 'token_type': 'bearer'},
            {'id': '1000', 'name': 'Empresa Demo'},
        ]),
    )
    datos = adaptador.exchange_code('codigo-oauth', 'http://localhost/callback')
    assert datos['access_token'] == 'largo-duracion'
    assert datos['expires_in'] == 5184000
    assert datos['external_user_id'] == '1000'
    assert datos['external_user_label'] == 'Empresa Demo'
    assert datos['refresh_token'] is None


def test_meta_get_accounts_facebook_lista_paginas(monkeypatch):
    adaptador = MetaAdapter('facebook')
    monkeypatch.setattr(
        'app.services.social.providers.meta.solicitar',
        _secuencia([
            {'data': [{'id': 'pagina-1', 'name': 'Mi Página', 'access_token': 'tok-pagina'}]},
        ]),
    )
    cuentas = adaptador.get_accounts('token-usuario')
    assert cuentas == [{
        'id_externo': 'pagina-1', 'nombre': 'Mi Página', 'usuario': None, 'url_imagen': None, 'metadatos': {},
    }]


def test_meta_get_accounts_instagram_resuelve_cuenta_vinculada(monkeypatch):
    adaptador = MetaAdapter('instagram')
    monkeypatch.setattr(
        'app.services.social.providers.meta.solicitar',
        _secuencia([
            {'data': [{'id': 'pagina-1', 'name': 'Mi Página', 'access_token': 'tok-pagina'}]},
            {'instagram_business_account': {'id': 'ig-1'}},
            {'username': 'mi_empresa', 'name': 'Mi Empresa', 'profile_picture_url': 'http://img'},
        ]),
    )
    cuentas = adaptador.get_accounts('token-usuario')
    assert cuentas[0]['id_externo'] == 'ig-1'
    assert cuentas[0]['usuario'] == 'mi_empresa'
    assert cuentas[0]['metadatos'] == {'pagina_id': 'pagina-1'}


def test_meta_refresh_token_no_soportado_lanza_error():
    adaptador = MetaAdapter('facebook')
    with pytest.raises(SocialProviderError) as exc_info:
        adaptador.refresh_token('cualquier-cosa')
    assert exc_info.value.tipo == 'refresh_expirado'


def test_meta_revoke_llama_delete_permissions(monkeypatch):
    llamadas = []

    def _fake(metodo, url, **kwargs):
        llamadas.append((metodo, url))
        return {'success': True}

    monkeypatch.setattr('app.services.social.providers.meta.solicitar', _fake)
    adaptador = MetaAdapter('facebook')
    assert adaptador.revoke('token') is True
    assert llamadas[0][0] == 'DELETE'
    assert 'me/permissions' in llamadas[0][1]


@pytest.mark.parametrize('codigo,subcodigo,tipo_esperado', [
    (190, 460, 'permisos_revocados'),
    (190, 463, 'token_expirado'),
    (4, None, 'limite_tasa'),
])
def test_clasificar_meta_mapea_codigos_conocidos(codigo, subcodigo, tipo_esperado):
    cuerpo = {'error': {'code': codigo, 'error_subcode': subcodigo}}
    assert _clasificar_meta(400, cuerpo) == tipo_esperado


def test_tiktok_authorize_url_incluye_pkce():
    adaptador = TikTokAdapter()
    url = adaptador.build_authorize_url('estado', 'http://localhost/callback', code_challenge='reto-pkce')
    assert 'code_challenge=reto-pkce' in url
    assert 'code_challenge_method=S256' in url


def test_tiktok_exchange_code_incluye_refresh_token(monkeypatch):
    adaptador = TikTokAdapter()
    monkeypatch.setattr(
        'app.services.social.providers.tiktok.solicitar',
        _secuencia([
            {
                'access_token': 'tok-1', 'refresh_token': 'refresh-1', 'expires_in': 86400,
                'refresh_expires_in': 31536000, 'open_id': 'open-1', 'scope': 'user.info.basic',
            },
            {'data': {'user': {'open_id': 'open-1', 'display_name': 'Cuenta Demo'}}},
        ]),
    )
    datos = adaptador.exchange_code('codigo', 'http://localhost/callback', code_verifier='verifier')
    assert datos['refresh_token'] == 'refresh-1'
    assert datos['external_user_id'] == 'open-1'
    assert datos['external_user_label'] == 'Cuenta Demo'


def test_tiktok_refresh_token_devuelve_nuevo_refresh_token_distinto(monkeypatch):
    adaptador = TikTokAdapter()
    monkeypatch.setattr(
        'app.services.social.providers.tiktok.solicitar',
        _secuencia([
            {'access_token': 'tok-nuevo', 'refresh_token': 'refresh-nuevo', 'expires_in': 86400, 'refresh_expires_in': 31536000},
        ]),
    )
    datos = adaptador.refresh_token('refresh-viejo')
    assert datos['refresh_token'] == 'refresh-nuevo'
    assert datos['refresh_token'] != 'refresh-viejo'


def test_tiktok_sync_posts_mapea_metricas(monkeypatch):
    adaptador = TikTokAdapter()
    monkeypatch.setattr(
        'app.services.social.providers.tiktok.solicitar',
        _secuencia([
            {'data': {'videos': [{
                'id': 'video-1', 'video_description': 'Hola', 'create_time': 1700000000,
                'share_url': 'https://tiktok.com/v/1', 'view_count': 1000, 'like_count': 50,
                'comment_count': 5, 'share_count': 2,
            }]}},
        ]),
    )
    posts = adaptador.sync_posts('token', account=None)
    assert posts[0]['metricas']['vistas'] == 1000
    assert posts[0]['metricas']['impresiones'] is None


def test_clasificar_tiktok_mapea_errores():
    assert _clasificar_tiktok(401, {'error': {'code': 'access_token_expired'}}) == 'token_expirado'
    assert _clasificar_tiktok(401, {'error': {'code': 'refresh_token_invalid'}}) == 'refresh_expirado'


def test_youtube_authorize_url_pide_acceso_offline():
    adaptador = YouTubeAdapter()
    url = adaptador.build_authorize_url('estado', 'http://localhost/callback')
    assert 'access_type=offline' in url
    assert 'prompt=consent' in url


def test_youtube_exchange_code_sin_refresh_token_lanza_error(monkeypatch):
    adaptador = YouTubeAdapter()
    monkeypatch.setattr(
        'app.services.social.providers.youtube.solicitar',
        _secuencia([{'access_token': 'tok', 'expires_in': 3600}]),
    )
    with pytest.raises(SocialProviderError):
        adaptador.exchange_code('codigo', 'http://localhost/callback')


def test_youtube_exchange_code_ok(monkeypatch):
    adaptador = YouTubeAdapter()
    monkeypatch.setattr(
        'app.services.social.providers.youtube.solicitar',
        _secuencia([
            {'access_token': 'tok', 'refresh_token': 'refresh', 'expires_in': 3600},
            {'items': [{'id': 'canal-1', 'snippet': {'title': 'Mi Canal'}, 'statistics': {}}]},
        ]),
    )
    datos = adaptador.exchange_code('codigo', 'http://localhost/callback')
    assert datos['external_user_id'] == 'canal-1'
    assert datos['external_user_label'] == 'Mi Canal'


def test_youtube_sync_profile_seguidores_ocultos_es_no_disponible(monkeypatch):
    adaptador = YouTubeAdapter()
    monkeypatch.setattr(
        'app.services.social.providers.youtube.solicitar',
        _secuencia([
            {'items': [{
                'id': 'canal-1', 'snippet': {'title': 'Mi Canal'},
                'statistics': {'hiddenSubscriberCount': True, 'viewCount': '500', 'videoCount': '10'},
            }]},
        ]),
    )
    perfil = adaptador.sync_profile('token', account=None)
    assert perfil['seguidores'] is None
    assert perfil['vistas_totales'] == 500


def test_clasificar_google_mapea_invalid_grant():
    assert _clasificar_google(400, {'error': 'invalid_grant'}) == 'refresh_expirado'
