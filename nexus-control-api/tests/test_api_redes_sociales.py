import os
from datetime import timedelta

from conftest import auth_headers, login

from app.extensions import db
from app.models import SocialAccount, SocialConnection, SocialOAuthState, _now_utc
from app.services.social import oauth_state
from app.services.social.providers.base import SocialProvider


def _h(client, user):
    return auth_headers(login(client, user.username).get_json()['token'])


class _ProveedorFalso(SocialProvider):
    platform_id = 'facebook'
    usa_pkce = False

    def build_authorize_url(self, state, redirect_uri, code_challenge=None):
        return f'https://facebook.example/oauth?state={state}'

    def exchange_code(self, code, redirect_uri, code_verifier=None):
        return {'access_token': 'tok-callback', 'expires_in': 3600, 'external_user_id': 'u1', 'external_user_label': 'Empresa'}

    def refresh_token(self, refresh_token):
        return {'access_token': 'tok-refrescado', 'expires_in': 3600}

    def get_accounts(self, access_token):
        return [{'id_externo': 'pagina-1', 'nombre': 'Página de prueba', 'usuario': None, 'url_imagen': None, 'metadatos': {}}]

    def sync_profile(self, access_token, account):
        return {'seguidores': 500}

    def sync_posts(self, access_token, account, limite=25):
        return []

    def revoke(self, access_token, refresh_token=None):
        return True

    def check_connection(self, access_token):
        return True


def test_requiere_sesion(client):
    r = client.get('/api/redes-sociales')
    assert r.status_code == 401


def test_listar_devuelve_cuatro_plataformas_desconectadas(client, admin):
    r = client.get('/api/redes-sociales', headers=_h(client, admin))
    assert r.status_code == 200
    body = r.get_json()
    assert sorted(c['plataforma'] for c in body) == ['facebook', 'instagram', 'tiktok', 'youtube']
    assert all(c['estado'] == 'DISCONNECTED' for c in body)
    assert all(c['conectada'] is False for c in body)


def test_admin_normal_no_puede_iniciar_conexion(client, admin):
    r = client.get('/api/redes-sociales/facebook/conectar', headers=_h(client, admin))
    assert r.status_code == 403


def test_super_admin_obtiene_url_de_autorizacion(client, super_admin):
    r = client.get('/api/redes-sociales/facebook/conectar', headers=_h(client, super_admin))
    assert r.status_code == 200
    body = r.get_json()
    assert body['url'].startswith('https://www.facebook.com/')
    assert SocialOAuthState.query.count() == 1


def test_conectar_instagram_usa_su_propia_redirect_uri(client, super_admin):
    r = client.get('/api/redes-sociales/instagram/conectar', headers=_h(client, super_admin))
    assert r.status_code == 200
    fila = SocialOAuthState.query.filter_by(plataforma='instagram').first()
    assert fila.redirect_uri.endswith('/callback/instagram')
    assert fila.redirect_uri != os.environ['META_REDIRECT_URI']
    assert fila.redirect_uri == os.environ['META_INSTAGRAM_REDIRECT_URI']


def test_conectar_plataforma_no_soportada(client, super_admin):
    r = client.get('/api/redes-sociales/x/conectar', headers=_h(client, super_admin))
    assert r.status_code == 400


def test_conectar_tiktok_genera_pkce(client, super_admin):
    r = client.get('/api/redes-sociales/tiktok/conectar', headers=_h(client, super_admin))
    assert r.status_code == 200
    fila = SocialOAuthState.query.filter_by(plataforma='tiktok').first()
    assert fila.code_verifier is not None
    assert 'code_challenge=' in r.get_json()['url']


def test_conectar_sin_configuracion_de_app(client, super_admin, monkeypatch):
    monkeypatch.delenv('META_APP_ID', raising=False)
    r = client.get('/api/redes-sociales/facebook/conectar', headers=_h(client, super_admin))
    assert r.status_code == 409


def test_callback_con_estado_invalido_redirige_con_error(client):
    r = client.get('/api/redes-sociales/callback/facebook?code=abc&state=no-existe')
    assert r.status_code == 302
    assert 'error=estado_invalido' in r.headers['Location']


def test_callback_con_autorizacion_rechazada_redirige_con_error(client):
    r = client.get('/api/redes-sociales/callback/facebook?error=access_denied')
    assert r.status_code == 302
    assert 'error=autorizacion_rechazada' in r.headers['Location']


def test_callback_exitoso_crea_conexion_y_sincroniza(client, super_admin, app, monkeypatch):
    monkeypatch.setattr('app.services.social.orchestrator.proveedor_para', lambda p: _ProveedorFalso())
    monkeypatch.setattr('app.routes.api_redes_sociales.endpoints.proveedor_para', lambda p: _ProveedorFalso())

    valor_estado = oauth_state.crear_estado('facebook', super_admin.id, 'http://localhost/callback')
    r = client.get(f'/api/redes-sociales/callback/facebook?code=codigo-x&state={valor_estado}')
    assert r.status_code == 302
    assert 'conectado=facebook' in r.headers['Location']

    conexion = SocialConnection.query.filter_by(plataforma='facebook').first()
    assert conexion is not None
    assert conexion.conectada() is True
    assert conexion.conectado_por == super_admin.username
    assert SocialAccount.query.filter_by(plataforma='facebook').count() == 1


def test_callback_instagram_exitoso_no_se_confunde_con_facebook(client, super_admin, app, monkeypatch):
    monkeypatch.setattr('app.services.social.orchestrator.proveedor_para', lambda p: _ProveedorFalso())
    monkeypatch.setattr('app.routes.api_redes_sociales.endpoints.proveedor_para', lambda p: _ProveedorFalso())

    r_conectar = client.get('/api/redes-sociales/instagram/conectar', headers=_h(client, super_admin))
    valor_estado = r_conectar.get_json()['url'].split('state=')[1]

    r = client.get(f'/api/redes-sociales/callback/instagram?code=codigo-x&state={valor_estado}')
    assert r.status_code == 302
    assert 'conectado=instagram' in r.headers['Location']

    conexion = SocialConnection.query.filter_by(plataforma='instagram').first()
    assert conexion is not None
    assert conexion.conectada() is True
    assert SocialConnection.query.filter_by(plataforma='facebook').first() is None


def test_sincronizar_sin_conexion_devuelve_409(client, admin):
    r = client.post('/api/redes-sociales/facebook/sincronizar', headers=_h(client, admin))
    assert r.status_code == 409


def _crear_conexion_activa(plataforma='facebook'):
    conexion = SocialConnection(plataforma=plataforma, estado='CONNECTED')
    conexion.access_token_cifrado = 'token-valido'
    conexion.expira_at = _now_utc() + timedelta(hours=2)
    db.session.add(conexion)
    db.session.commit()
    return conexion


def test_sincronizar_manual_exitoso(client, admin, app, monkeypatch):
    monkeypatch.setattr('app.services.social.orchestrator.proveedor_para', lambda p: _ProveedorFalso())
    _crear_conexion_activa('facebook')

    r = client.post('/api/redes-sociales/facebook/sincronizar', headers=_h(client, admin))
    assert r.status_code == 200
    body = r.get_json()
    assert body['ok'] is True
    assert body['conexion']['estado'] == 'CONNECTED'


def test_sincronizar_respeta_cooldown(client, admin, app):
    conexion = _crear_conexion_activa('facebook')
    conexion.bloqueado_hasta = _now_utc() + timedelta(seconds=30)
    db.session.commit()

    r = client.post('/api/redes-sociales/facebook/sincronizar', headers=_h(client, admin))
    assert r.status_code == 429


def test_desconectar_requiere_super_admin(client, admin):
    _crear_conexion_activa('facebook')
    r = client.post('/api/redes-sociales/facebook/desconectar', headers=_h(client, admin))
    assert r.status_code == 403


def test_desconectar_conserva_historico_por_defecto(client, super_admin, app, monkeypatch):
    monkeypatch.setattr(
        'app.services.social.providers.proveedor_para',
        lambda p: _ProveedorFalso(),
    )
    conexion = _crear_conexion_activa('facebook')
    cuenta = SocialAccount(connection_id=conexion.id, plataforma='facebook', id_externo='pagina-1', nombre='Página')
    db.session.add(cuenta)
    db.session.commit()

    r = client.post('/api/redes-sociales/facebook/desconectar', json={}, headers=_h(client, super_admin))
    assert r.status_code == 200

    conexion_recargada = SocialConnection.query.filter_by(plataforma='facebook').first()
    assert conexion_recargada is not None
    assert conexion_recargada.access_token_cifrado is None
    assert conexion_recargada.estado == 'DISCONNECTED'
    assert SocialAccount.query.filter_by(plataforma='facebook').count() == 1


def test_desconectar_purga_historico_si_se_solicita(client, super_admin, app, monkeypatch):
    monkeypatch.setattr(
        'app.services.social.providers.proveedor_para',
        lambda p: _ProveedorFalso(),
    )
    conexion = _crear_conexion_activa('facebook')
    cuenta = SocialAccount(connection_id=conexion.id, plataforma='facebook', id_externo='pagina-1', nombre='Página')
    db.session.add(cuenta)
    db.session.commit()

    r = client.post('/api/redes-sociales/facebook/desconectar', json={'purgar_historico': True}, headers=_h(client, super_admin))
    assert r.status_code == 200
    assert SocialConnection.query.filter_by(plataforma='facebook').count() == 0
    assert SocialAccount.query.filter_by(plataforma='facebook').count() == 0


def test_salud_de_plataforma_no_conectada(client, admin):
    r = client.get('/api/redes-sociales/facebook/salud', headers=_h(client, admin))
    assert r.status_code == 200
    assert r.get_json()['estado'] == 'DISCONNECTED'


def test_sistema_devuelve_intervalo_y_plataformas(client, admin):
    r = client.get('/api/redes-sociales/sistema', headers=_h(client, admin))
    assert r.status_code == 200
    body = r.get_json()
    assert body['intervalo_minutos'] == 15
    assert len(body['plataformas']) == 4


def test_resumen_rango_predefinido(client, admin):
    r = client.get('/api/redes-sociales/resumen?rango=7d', headers=_h(client, admin))
    assert r.status_code == 200
    body = r.get_json()
    assert 'narrativa' in body
    assert body['publicaciones'] == 0


def test_resumen_rango_custom_invalido(client, admin):
    r = client.get('/api/redes-sociales/resumen?rango=custom', headers=_h(client, admin))
    assert r.status_code == 400


def test_resumen_rango_desconocido(client, admin):
    r = client.get('/api/redes-sociales/resumen?rango=1y', headers=_h(client, admin))
    assert r.status_code == 400


def test_seguimiento_de_cuenta_requiere_super_admin(client, admin, app):
    conexion = _crear_conexion_activa('facebook')
    cuenta = SocialAccount(connection_id=conexion.id, plataforma='facebook', id_externo='pagina-1', nombre='Página')
    db.session.add(cuenta)
    db.session.commit()

    r = client.put(
        f'/api/redes-sociales/facebook/cuentas/{cuenta.id}/seguimiento',
        json={'seguimiento_activo': False}, headers=_h(client, admin),
    )
    assert r.status_code == 403


def test_seguimiento_de_cuenta_actualiza_bandera(client, super_admin, app):
    conexion = _crear_conexion_activa('facebook')
    cuenta = SocialAccount(connection_id=conexion.id, plataforma='facebook', id_externo='pagina-1', nombre='Página')
    db.session.add(cuenta)
    db.session.commit()

    r = client.put(
        f'/api/redes-sociales/facebook/cuentas/{cuenta.id}/seguimiento',
        json={'seguimiento_activo': False}, headers=_h(client, super_admin),
    )
    assert r.status_code == 200
    db.session.refresh(cuenta)
    assert cuenta.seguimiento_activo is False
