import pyotp
from conftest import auth_headers, login

from app.extensions import db
from app.models import TwoFactorBackupCode, User

PASSWORD = 'Cl4ve-Segura-Prueba!'


def _token(client, user):
    return login(client, user.username).get_json()['token']


def _activar_2fa(client, admin):
    token = _token(client, admin)
    h = auth_headers(token)
    setup = client.post('/api/auth/setup-2fa', json={'current_password': PASSWORD}, headers=h)
    secret = setup.get_json()['secret']
    code = pyotp.TOTP(secret).now()
    confirm = client.post(
        '/api/auth/confirm-2fa',
        json={'current_password': PASSWORD, 'secret': secret, 'code': code},
        headers=h,
    )
    assert confirm.status_code == 200
    db.session.refresh(admin)
    return secret


def test_setup_2fa_rechaza_password_incorrecta(client, admin):
    h = auth_headers(_token(client, admin))
    r = client.post('/api/auth/setup-2fa', json={'current_password': 'mala'}, headers=h)
    assert r.status_code == 401


def test_setup_2fa_devuelve_secret_y_qr(client, admin):
    h = auth_headers(_token(client, admin))
    r = client.post('/api/auth/setup-2fa', json={'current_password': PASSWORD}, headers=h)
    assert r.status_code == 200
    body = r.get_json()
    assert len(body['secret']) >= 16
    assert body['qr']


def test_confirm_2fa_activa_la_cuenta_y_revoca_sesiones_previas(client, admin):
    login(client, admin.username)
    _activar_2fa(client, admin)
    assert admin.totp_secret
    from app.models import RefreshToken
    assert RefreshToken.query.filter_by(user_id=admin.id, revoked=False).count() == 0


def test_confirm_2fa_codigo_incorrecto(client, admin):
    token = _token(client, admin)
    h = auth_headers(token)
    setup = client.post('/api/auth/setup-2fa', json={'current_password': PASSWORD}, headers=h)
    secret = setup.get_json()['secret']
    r = client.post(
        '/api/auth/confirm-2fa',
        json={'current_password': PASSWORD, 'secret': secret, 'code': '000000'},
        headers=h,
    )
    assert r.status_code == 400


def test_login_con_2fa_activo_pide_step_token(client, admin):
    _activar_2fa(client, admin)
    r = login(client, admin.username)
    assert r.status_code == 200
    body = r.get_json()
    assert body['requires2fa'] is True
    assert body['stepToken']
    assert 'token' not in body


def test_verify_2fa_codigo_correcto_completa_el_login(client, admin):
    secret = _activar_2fa(client, admin)
    step = login(client, admin.username).get_json()['stepToken']
    code = pyotp.TOTP(secret).now()
    r = client.post('/api/auth/verify-2fa', json={'stepToken': step, 'code': code})
    assert r.status_code == 200
    assert r.get_json()['token']


def test_verify_2fa_codigo_incorrecto(client, admin):
    _activar_2fa(client, admin)
    step = login(client, admin.username).get_json()['stepToken']
    r = client.post('/api/auth/verify-2fa', json={'stepToken': step, 'code': '000000'})
    assert r.status_code == 401


def test_verify_2fa_mismo_codigo_no_se_puede_reutilizar(client, admin):
    secret = _activar_2fa(client, admin)
    step1 = login(client, admin.username).get_json()['stepToken']
    code = pyotp.TOTP(secret).now()
    ok = client.post('/api/auth/verify-2fa', json={'stepToken': step1, 'code': code})
    assert ok.status_code == 200

    step2 = login(client, admin.username).get_json()['stepToken']
    r = client.post('/api/auth/verify-2fa', json={'stepToken': step2, 'code': code})
    assert r.status_code == 401
    assert 'ya fue usado' in r.get_json()['error']


def test_verify_2fa_step_token_no_reutilizable(client, admin):
    secret = _activar_2fa(client, admin)
    step = login(client, admin.username).get_json()['stepToken']
    code1 = pyotp.TOTP(secret).now()
    client.post('/api/auth/verify-2fa', json={'stepToken': step, 'code': code1})

    import time
    time.sleep(1)
    code2 = pyotp.TOTP(secret).now()
    while code2 == code1:
        time.sleep(1)
        code2 = pyotp.TOTP(secret).now()
    r = client.post('/api/auth/verify-2fa', json={'stepToken': step, 'code': code2})
    assert r.status_code == 401


def test_verify_2fa_bloquea_tras_varios_fallos(client, admin):
    _activar_2fa(client, admin)
    step = login(client, admin.username).get_json()['stepToken']
    for i in range(5):
        client.post(
            '/api/auth/verify-2fa',
            json={'stepToken': step, 'code': '000000'},
            environ_overrides={'REMOTE_ADDR': f'10.1.0.{i}'},
        )
    r = client.post(
        '/api/auth/verify-2fa',
        json={'stepToken': step, 'code': '000000'},
        environ_overrides={'REMOTE_ADDR': '10.1.0.99'},
    )
    assert r.status_code == 423


def test_disable_2fa(client, admin):
    secret = _activar_2fa(client, admin)
    token, usado = _verificar(client, admin, secret)
    h = auth_headers(token)
    r = client.post('/api/auth/disable-2fa', json={'current_password': PASSWORD, 'code': _codigo_fresco(secret, evitar=usado)}, headers=h)
    assert r.status_code == 200
    db.session.refresh(admin)
    assert admin.totp_secret is None
    assert TwoFactorBackupCode.query.filter_by(user_id=admin.id).count() == 0


def _codigo_fresco(secret, evitar=None):
    import time
    codigo = pyotp.TOTP(secret).now()
    while codigo == evitar:
        time.sleep(1)
        codigo = pyotp.TOTP(secret).now()
    return codigo


def _verificar(client, admin, secret):
    step = login(client, admin.username).get_json()['stepToken']
    code = _codigo_fresco(secret)
    r = client.post('/api/auth/verify-2fa', json={'stepToken': step, 'code': code})
    return r.get_json()['token'], code


def test_backup_codes_status_sin_2fa(client, admin):
    h = auth_headers(_token(client, admin))
    r = client.get('/api/auth/backup-codes', headers=h)
    assert r.get_json() == {'enabled': False, 'remaining': 0}


def test_generar_y_consumir_backup_code(client, admin):
    secret = _activar_2fa(client, admin)
    token, usado = _verificar(client, admin, secret)
    h = auth_headers(token)

    r = client.post(
        '/api/auth/backup-codes',
        json={'current_password': PASSWORD, 'code': _codigo_fresco(secret, evitar=usado)},
        headers=h,
    )
    assert r.status_code == 200
    codigos = r.get_json()['codes']
    assert len(codigos) == 10

    step = login(client, admin.username).get_json()['stepToken']
    usar = client.post('/api/auth/verify-2fa', json={'stepToken': step, 'code': codigos[0]})
    assert usar.status_code == 200

    step2 = login(client, admin.username).get_json()['stepToken']
    reutilizar = client.post('/api/auth/verify-2fa', json={'stepToken': step2, 'code': codigos[0]})
    assert reutilizar.status_code == 401


def test_estado_de_backup_codes_bajo(client, admin):
    secret = _activar_2fa(client, admin)
    token, usado = _verificar(client, admin, secret)
    h = auth_headers(token)
    client.post(
        '/api/auth/backup-codes',
        json={'current_password': PASSWORD, 'code': _codigo_fresco(secret, evitar=usado)},
        headers=h,
    )
    codigos = TwoFactorBackupCode.query.filter_by(user_id=admin.id).all()
    for c in codigos[:8]:
        c.consumed_at = db.func.now()
    db.session.commit()
    r = client.get('/api/auth/backup-codes', headers=h)
    body = r.get_json()
    assert body['remaining'] == 2
    assert body['low'] is True
