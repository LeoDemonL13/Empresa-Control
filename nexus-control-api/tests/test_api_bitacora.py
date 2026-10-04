from conftest import auth_headers, login

from app.extensions import db
from app.utils import log_action


def _h(client, user):
    return auth_headers(login(client, user.username).get_json()['token'])


def test_listar_bitacora_requiere_sesion(client):
    r = client.get('/api/bitacora')
    assert r.status_code == 401


def test_admin_puede_ver_la_bitacora(client, admin):
    r = client.get('/api/bitacora', headers=_h(client, admin))
    assert r.status_code == 200
    body = r.get_json()
    assert body['total'] >= 1
    assert body['page'] == 1


def test_paginacion_de_la_bitacora(client, admin, app):
    with app.test_request_context('/'):
        for i in range(25):
            log_action(f'evento de prueba {i}', entidad='prueba', entidad_id=i)
    r = client.get('/api/bitacora?per_page=10&page=2', headers=_h(client, admin))
    body = r.get_json()
    assert len(body['items']) == 10
    assert body['page'] == 2
    assert body['has_prev'] is True


def test_filtrar_bitacora_por_entidad(client, admin, app):
    with app.test_request_context('/'):
        log_action('acción sobre un equipo', entidad='equipo', entidad_id=1)
    r = client.get('/api/bitacora?entidad=equipo', headers=_h(client, admin))
    body = r.get_json()
    assert all(item['entidad'] == 'equipo' for item in body['items'])
    assert body['total'] >= 1


def test_filtrar_bitacora_por_usuario(client, admin, super_admin):
    login(client, super_admin.username)
    r = client.get(f'/api/bitacora?user={admin.username}', headers=_h(client, admin))
    body = r.get_json()
    assert all(item['user'] == admin.username for item in body['items'])


def test_detalle_de_un_registro_de_bitacora(client, admin, app):
    with app.test_request_context('/'):
        log_action('acción con detalle', entidad='equipo', entidad_id=9, detalle={'antes': None, 'despues': {'nombre': 'PC-01'}})
    lista = client.get('/api/bitacora?entidad=equipo', headers=_h(client, admin)).get_json()
    log_id = lista['items'][0]['id']
    r = client.get(f'/api/bitacora/{log_id}', headers=_h(client, admin))
    assert r.status_code == 200
    assert r.get_json()['detalle']['despues']['nombre'] == 'PC-01'


def test_detalle_de_registro_inexistente(client, admin):
    r = client.get('/api/bitacora/999999', headers=_h(client, admin))
    assert r.status_code == 404
