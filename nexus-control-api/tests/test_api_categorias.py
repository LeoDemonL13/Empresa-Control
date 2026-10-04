from conftest import auth_headers, login


def _h(client, user):
    return auth_headers(login(client, user.username).get_json()['token'])


def test_listar_categorias_vacia(client, admin):
    r = client.get('/api/categorias', headers=_h(client, admin))
    assert r.status_code == 200
    assert r.get_json() == []


def test_listar_categorias_con_conteo_de_equipos(client, admin):
    h = _h(client, admin)
    client.post('/api/equipos', json={'nombre': 'PC-1', 'categoria': 'Ventas'}, headers=h)
    client.post('/api/equipos', json={'nombre': 'PC-2', 'categoria': 'Ventas'}, headers=h)
    client.post('/api/equipos', json={'nombre': 'PC-3', 'categoria': 'Soporte'}, headers=h)

    r = client.get('/api/categorias', headers=h)
    por_nombre = {c['nombre']: c['total_equipos'] for c in r.get_json()}
    assert por_nombre == {'Soporte': 1, 'Ventas': 2}


def test_categorias_requiere_sesion(client):
    r = client.get('/api/categorias')
    assert r.status_code == 401
