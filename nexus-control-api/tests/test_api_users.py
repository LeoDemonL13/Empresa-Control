from conftest import auth_headers, login

from app.extensions import db
from app.models import RefreshToken, User

PASSWORD = 'Cl4ve-Segura-Prueba!'


def _h(client, user):
    return auth_headers(login(client, user.username).get_json()['token'])


def test_solo_super_admin_puede_listar_administradores(client, admin):
    r = client.get('/api/users', headers=_h(client, admin))
    assert r.status_code == 403


def test_super_admin_lista_administradores(client, super_admin, admin):
    r = client.get('/api/users', headers=_h(client, super_admin))
    assert r.status_code == 200
    usuarios = r.get_json()
    assert {u['username'] for u in usuarios} == {super_admin.username, admin.username}


def test_crear_administrador(client, super_admin):
    r = client.post('/api/users', json={
        'username': 'nuevo@nexus.mx',
        'password': 'Cl4ve-Valida-2026!',
        'full_name': 'Nuevo Admin',
    }, headers=_h(client, super_admin))
    assert r.status_code == 201
    body = r.get_json()
    assert body['role'] == 'admin'
    assert 'password_hash' not in body


def test_crear_administrador_username_duplicado(client, super_admin, admin):
    r = client.post('/api/users', json={
        'username': admin.username,
        'password': 'Cl4ve-Valida-2026!',
    }, headers=_h(client, super_admin))
    assert r.status_code == 409


def test_crear_administrador_password_debil(client, super_admin):
    r = client.post('/api/users', json={'username': 'x@nexus.mx', 'password': 'corta'}, headers=_h(client, super_admin))
    assert r.status_code == 400


def test_admin_no_puede_crear_administradores(client, admin):
    r = client.post('/api/users', json={'username': 'x@nexus.mx', 'password': 'Cl4ve-Valida-2026!'}, headers=_h(client, admin))
    assert r.status_code == 403


def test_actualizar_datos_de_un_administrador(client, super_admin, admin):
    r = client.put(f'/api/users/{admin.id}', json={'position': 'Soporte'}, headers=_h(client, super_admin))
    assert r.status_code == 200
    assert r.get_json()['position'] == 'Soporte'


def test_desactivar_administrador_revoca_sus_sesiones(client, super_admin, admin):
    login(client, admin.username)
    r = client.delete(f'/api/users/{admin.id}', headers=_h(client, super_admin))
    assert r.status_code == 200
    db.session.refresh(admin)
    assert admin.activo is False
    assert RefreshToken.query.filter_by(user_id=admin.id, revoked=False).count() == 0


def test_no_se_puede_desactivar_la_propia_cuenta(client, super_admin):
    r = client.delete(f'/api/users/{super_admin.id}', headers=_h(client, super_admin))
    assert r.status_code == 400


def test_no_se_puede_desactivar_al_ultimo_super_admin(client, super_admin):
    otro = User(username='otro_super@nexus.mx', password_hash=super_admin.password_hash, role='super_admin', activo=True)
    db.session.add(otro)
    db.session.commit()
    h = _h(client, super_admin)
    r1 = client.delete(f'/api/users/{otro.id}', headers=h)
    assert r1.status_code == 200
    otro2 = User(username='otro_super2@nexus.mx', password_hash=super_admin.password_hash, role='super_admin', activo=True)
    db.session.add(otro2)
    db.session.commit()
    login(client, otro2.username)
    h2 = _h(client, super_admin)
    r2 = client.delete(f'/api/users/{otro2.id}', headers=h2)
    assert r2.status_code == 200


def test_reactivar_administrador(client, super_admin, admin):
    client.delete(f'/api/users/{admin.id}', headers=_h(client, super_admin))
    r = client.post(f'/api/users/{admin.id}/reactivar', headers=_h(client, super_admin))
    assert r.status_code == 200
    assert r.get_json()['activo'] is True


def test_super_admin_resetea_password_de_un_administrador(client, super_admin, admin):
    nueva = 'Restablecida-Segura-9!'
    r = client.post(f'/api/users/{admin.id}/password', json={'new_password': nueva}, headers=_h(client, super_admin))
    assert r.status_code == 200
    assert login(client, admin.username, password=nueva).status_code == 200


def test_admin_no_puede_resetear_password_de_otros(client, admin, super_admin):
    r = client.post(f'/api/users/{super_admin.id}/password', json={'new_password': 'Otra-Segura-99!'}, headers=_h(client, admin))
    assert r.status_code == 403


def test_super_admin_puede_revocar_sesiones_de_un_administrador(client, super_admin, admin):
    login(client, admin.username)
    r = client.delete(f'/api/users/{admin.id}/sessions', headers=_h(client, super_admin))
    assert r.status_code == 200
    assert RefreshToken.query.filter_by(user_id=admin.id, revoked=False).count() == 0
