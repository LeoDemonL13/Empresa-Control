from conftest import auth_headers, login

from app.extensions import db
from app.models import RefreshToken

PASSWORD = 'Cl4ve-Segura-Prueba!'


def _token(client, user):
    return login(client, user.username).get_json()['token']


def test_perfil_devuelve_los_datos_del_usuario_autenticado(client, admin):
    h = auth_headers(_token(client, admin))
    r = client.get('/api/auth/perfil', headers=h)
    assert r.status_code == 200
    assert r.get_json()['username'] == admin.username


def test_actualizar_perfil(client, admin):
    h = auth_headers(_token(client, admin))
    r = client.put('/api/auth/perfil', json={'full_name': 'Ana Actualizada', 'position': 'Operaciones'}, headers=h)
    assert r.status_code == 200
    body = r.get_json()
    assert body['full_name'] == 'Ana Actualizada'
    assert body['position'] == 'Operaciones'


def test_actividad_reciente_del_perfil(client, admin):
    h = auth_headers(_token(client, admin))
    r = client.get('/api/auth/perfil/actividad', headers=h)
    assert r.status_code == 200
    assert isinstance(r.get_json(), list)
    assert len(r.get_json()) >= 1


def test_cambiar_password_requiere_la_actual_correcta(client, admin):
    h = auth_headers(_token(client, admin))
    r = client.put('/api/auth/perfil/password', json={'current_password': 'mala', 'new_password': 'Otra-Clave-Segura-99!'}, headers=h)
    assert r.status_code == 401


def test_cambiar_password_debil_es_rechazada(client, admin):
    h = auth_headers(_token(client, admin))
    r = client.put('/api/auth/perfil/password', json={'current_password': PASSWORD, 'new_password': 'corta'}, headers=h)
    assert r.status_code == 400


def test_cambiar_password_exitoso_revoca_sesiones_y_permite_login_nuevo(client, admin):
    login(client, admin.username)
    h = auth_headers(_token(client, admin))
    nueva = 'Otra-Clave-Segura-99!'
    r = client.put('/api/auth/perfil/password', json={'current_password': PASSWORD, 'new_password': nueva}, headers=h)
    assert r.status_code == 200
    assert RefreshToken.query.filter_by(user_id=admin.id, revoked=False).count() == 0
    r2 = login(client, admin.username, password=nueva)
    assert r2.status_code == 200


def test_listar_sesiones_activas(client, admin):
    login(client, admin.username)
    h = auth_headers(_token(client, admin))
    r = client.get('/api/auth/sesiones', headers=h)
    assert r.status_code == 200
    assert len(r.get_json()) == 2


def test_revocar_una_sesion(client, admin):
    login(client, admin.username)
    h = auth_headers(_token(client, admin))
    sesiones = client.get('/api/auth/sesiones', headers=h).get_json()
    r = client.delete(f"/api/auth/sesiones/{sesiones[0]['id']}", headers=h)
    assert r.status_code == 200
    restantes = client.get('/api/auth/sesiones', headers=h).get_json()
    assert len(restantes) == 1


def test_revocar_todas_las_sesiones_cierra_la_actual(client, admin):
    token = _token(client, admin)
    h = auth_headers(token)
    r = client.delete('/api/auth/sesiones', headers=h)
    assert r.status_code == 200
    r2 = client.get('/api/auth/perfil', headers=h)
    assert r2.status_code == 401


def test_estado_seguridad_reporta_redis_conectado(client, admin):
    h = auth_headers(_token(client, admin))
    r = client.get('/api/auth/estado-seguridad', headers=h)
    assert r.status_code == 200
    assert r.get_json()['redis']['ok'] is True
    assert r.get_json()['defensas_degradadas'] == []
