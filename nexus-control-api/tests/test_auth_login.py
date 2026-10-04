from conftest import auth_headers, login

from app.extensions import db
from app.models import RefreshToken, User


def test_login_exitoso_devuelve_token_y_usuario(client, admin):
    r = login(client, admin.username)
    assert r.status_code == 200
    body = r.get_json()
    assert body['user']['username'] == admin.username
    assert 'password_hash' not in body['user']
    assert body['token']
    assert 'rt_api' in r.headers.get('Set-Cookie', '')


def test_login_password_incorrecta(client, admin):
    r = client.post('/api/auth/login', json={'username': admin.username, 'password': 'incorrecta'})
    assert r.status_code == 401
    assert r.get_json() == {'error': 'Credenciales incorrectas'}


def test_login_usuario_inexistente_no_revela_nada(client):
    r = client.post('/api/auth/login', json={'username': 'nadie@nexus.mx', 'password': 'x' * 20})
    assert r.status_code == 401
    assert r.get_json() == {'error': 'Credenciales incorrectas'}


def test_login_cuenta_desactivada(client, admin):
    admin.activo = False
    db.session.commit()
    r = login(client, admin.username)
    assert r.status_code == 403


def test_login_bloquea_tras_varios_intentos_fallidos_del_mismo_usuario(client, admin):
    for i in range(5):
        client.post(
            '/api/auth/login',
            json={'username': admin.username, 'password': 'mala'},
            environ_overrides={'REMOTE_ADDR': f'10.0.0.{i}'},
        )
    r = client.post(
        '/api/auth/login',
        json={'username': admin.username, 'password': 'mala'},
        environ_overrides={'REMOTE_ADDR': '10.0.0.99'},
    )
    assert r.status_code == 423
    r2 = login(client, admin.username)
    assert r2.status_code == 423


def test_login_repetido_desde_una_ip_activa_el_limite_de_peticiones(client, admin):
    for _ in range(4):
        client.post('/api/auth/login', json={'username': admin.username, 'password': 'mala'})
    r = client.post('/api/auth/login', json={'username': admin.username, 'password': 'mala'})
    assert r.status_code == 429


def test_login_correcto_limpia_intentos_fallidos_previos(client, admin):
    for _ in range(3):
        client.post('/api/auth/login', json={'username': admin.username, 'password': 'mala'})
    r = login(client, admin.username)
    assert r.status_code == 200


def test_login_faltan_campos(client):
    r = client.post('/api/auth/login', json={'username': 'x'})
    assert r.status_code == 400


def test_jwt_required_sin_token(client):
    r = client.get('/api/auth/perfil')
    assert r.status_code == 401


def test_jwt_required_token_invalido(client):
    r = client.get('/api/auth/perfil', headers=auth_headers('esto-no-es-un-jwt'))
    assert r.status_code == 401


def test_jwt_required_acepta_token_valido(client, admin):
    token = login(client, admin.username).get_json()['token']
    r = client.get('/api/auth/perfil', headers=auth_headers(token))
    assert r.status_code == 200
    assert r.get_json()['username'] == admin.username


def test_jwt_required_rechaza_tras_cambio_de_password_version(client, admin):
    token = login(client, admin.username).get_json()['token']
    admin.password_version = (admin.password_version or 1) + 1
    db.session.commit()
    r = client.get('/api/auth/perfil', headers=auth_headers(token))
    assert r.status_code == 401


def test_jwt_required_rechaza_cuenta_desactivada_despues_de_emitir_token(client, admin):
    token = login(client, admin.username).get_json()['token']
    admin.activo = False
    db.session.commit()
    r = client.get('/api/auth/perfil', headers=auth_headers(token))
    assert r.status_code == 401


def test_logout_exige_header_csrf(client, admin):
    token = login(client, admin.username).get_json()['token']
    r = client.post('/api/auth/logout', headers=auth_headers(token))
    assert r.status_code == 403


def test_logout_revoca_el_token_de_acceso(client, admin):
    token = login(client, admin.username).get_json()['token']
    headers = auth_headers(token)
    headers['X-Requested-With'] = 'XMLHttpRequest'
    r = client.post('/api/auth/logout', headers=headers)
    assert r.status_code == 200
    r2 = client.get('/api/auth/perfil', headers=auth_headers(token))
    assert r2.status_code == 401


def test_refresh_rota_la_cookie_y_emite_nuevo_token(client, admin):
    login(client, admin.username)
    r = client.post('/api/auth/refresh', headers={'X-Requested-With': 'XMLHttpRequest'})
    assert r.status_code == 200
    assert r.get_json()['token']
    assert RefreshToken.query.filter_by(user_id=admin.id, revoked=False).count() == 1


def test_refresh_sin_cookie(client):
    r = client.post('/api/auth/refresh', headers={'X-Requested-With': 'XMLHttpRequest'})
    assert r.status_code == 401


def test_refresh_exige_header_csrf(client, admin):
    login(client, admin.username)
    r = client.post('/api/auth/refresh')
    assert r.status_code == 403


def test_refresh_de_token_ya_revocado_fuera_de_la_ventana_de_rotacion_revoca_la_familia(client, admin):
    login(client, admin.username)
    tok = RefreshToken.query.filter_by(user_id=admin.id, revoked=False).first()
    raw_original = client.get_cookie('rt_api', domain='localhost', path='/api/auth').value
    tok.revoked = True
    db.session.commit()

    client.set_cookie('rt_api', raw_original)
    r = client.post('/api/auth/refresh', headers={'X-Requested-With': 'XMLHttpRequest'})
    assert r.status_code == 401
    assert r.get_json() == {'error': 'Sesión comprometida. Vuelve a iniciar sesión.'}
    assert RefreshToken.query.filter_by(user_id=admin.id, revoked=False).count() == 0


def test_refresh_token_expirado_es_rechazado(client, admin, app):
    from datetime import datetime, timedelta, timezone

    login(client, admin.username)
    tok = RefreshToken.query.filter_by(user_id=admin.id, revoked=False).first()
    tok.expires_at = datetime.now(timezone.utc) - timedelta(days=1)
    db.session.commit()
    r = client.post('/api/auth/refresh', headers={'X-Requested-With': 'XMLHttpRequest'})
    assert r.status_code == 401
    assert db.session.get(RefreshToken, tok.id).revoked is True
