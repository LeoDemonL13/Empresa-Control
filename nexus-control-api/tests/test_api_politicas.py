from conftest import auth_headers, login

from app.extensions import db
from app.models import Aplicacion, Equipo, EquipoAppPolitica


def _h(client, user):
    return auth_headers(login(client, user.username).get_json()['token'])


def _crear_equipo(client, admin, nombre='PC-Politicas'):
    return client.post('/api/equipos', json={'nombre': nombre}, headers=_h(client, admin)).get_json()


def test_listar_aplicaciones_vacio(client, admin):
    creado = _crear_equipo(client, admin)
    r = client.get(f"/api/equipos/{creado['id']}/aplicaciones", headers=_h(client, admin))
    assert r.status_code == 200
    assert r.get_json() == []


def test_agregar_aplicacion_crea_politica_por_defecto(client, admin):
    creado = _crear_equipo(client, admin)
    r = client.post(
        f"/api/equipos/{creado['id']}/aplicaciones",
        json={'ejecutable': 'chrome.exe', 'nombre': 'Google Chrome'},
        headers=_h(client, admin),
    )
    assert r.status_code == 201
    body = r.get_json()
    assert body['aplicacion']['ejecutable'] == 'chrome.exe'
    assert body['estado'] == 'permitida'
    assert body['tipo_uso'] == 'sin_limite'
    assert Aplicacion.query.filter_by(ejecutable_normalizado='chrome.exe').count() == 1


def test_agregar_aplicacion_reutiliza_catalogo_existente(client, admin):
    h = _h(client, admin)
    e1 = _crear_equipo(client, admin, 'PC-Uno')
    e2 = _crear_equipo(client, admin, 'PC-Dos')
    client.post(f"/api/equipos/{e1['id']}/aplicaciones", json={'ejecutable': 'Discord.exe'}, headers=h)
    client.post(f"/api/equipos/{e2['id']}/aplicaciones", json={'ejecutable': 'discord.exe'}, headers=h)
    assert Aplicacion.query.filter_by(ejecutable_normalizado='discord.exe').count() == 1


def test_agregar_aplicacion_duplicada_en_el_mismo_equipo(client, admin):
    h = _h(client, admin)
    creado = _crear_equipo(client, admin)
    client.post(f"/api/equipos/{creado['id']}/aplicaciones", json={'ejecutable': 'steam.exe'}, headers=h)
    r = client.post(f"/api/equipos/{creado['id']}/aplicaciones", json={'ejecutable': 'steam.exe'}, headers=h)
    assert r.status_code == 409


def test_agregar_aplicacion_sin_ejecutable(client, admin):
    creado = _crear_equipo(client, admin)
    r = client.post(f"/api/equipos/{creado['id']}/aplicaciones", json={'ejecutable': '  '}, headers=_h(client, admin))
    assert r.status_code == 400


def test_bloquear_aplicacion(client, admin):
    h = _h(client, admin)
    creado = _crear_equipo(client, admin)
    app_creada = client.post(f"/api/equipos/{creado['id']}/aplicaciones", json={'ejecutable': 'juego.exe'}, headers=h).get_json()
    aplicacion_id = app_creada['aplicacion']['id']

    r = client.put(
        f"/api/equipos/{creado['id']}/aplicaciones/{aplicacion_id}",
        json={'estado': 'bloqueada'},
        headers=h,
    )
    assert r.status_code == 200
    assert r.get_json()['estado'] == 'bloqueada'

    equipo = db.session.get(Equipo, creado['id'])
    assert equipo.politica_version == 2


def test_asignar_limite_de_tiempo(client, admin):
    h = _h(client, admin)
    creado = _crear_equipo(client, admin)
    app_creada = client.post(f"/api/equipos/{creado['id']}/aplicaciones", json={'ejecutable': 'juego.exe'}, headers=h).get_json()
    aplicacion_id = app_creada['aplicacion']['id']

    r = client.put(
        f"/api/equipos/{creado['id']}/aplicaciones/{aplicacion_id}",
        json={'tipo_uso': 'con_limite', 'limite_minutos': 60},
        headers=h,
    )
    assert r.status_code == 200
    body = r.get_json()
    assert body['tipo_uso'] == 'con_limite'
    assert body['limite_minutos'] == 60


def test_asignar_limite_sin_minutos_es_rechazado(client, admin):
    h = _h(client, admin)
    creado = _crear_equipo(client, admin)
    app_creada = client.post(f"/api/equipos/{creado['id']}/aplicaciones", json={'ejecutable': 'juego.exe'}, headers=h).get_json()
    aplicacion_id = app_creada['aplicacion']['id']

    r = client.put(
        f"/api/equipos/{creado['id']}/aplicaciones/{aplicacion_id}",
        json={'tipo_uso': 'con_limite'},
        headers=h,
    )
    assert r.status_code == 400


def test_volver_a_sin_limite_borra_el_limite_anterior(client, admin):
    h = _h(client, admin)
    creado = _crear_equipo(client, admin)
    app_creada = client.post(f"/api/equipos/{creado['id']}/aplicaciones", json={'ejecutable': 'juego.exe'}, headers=h).get_json()
    aplicacion_id = app_creada['aplicacion']['id']

    client.put(
        f"/api/equipos/{creado['id']}/aplicaciones/{aplicacion_id}",
        json={'tipo_uso': 'con_limite', 'limite_minutos': 30},
        headers=h,
    )
    r = client.put(
        f"/api/equipos/{creado['id']}/aplicaciones/{aplicacion_id}",
        json={'tipo_uso': 'sin_limite'},
        headers=h,
    )
    assert r.get_json()['limite_minutos'] is None


def test_actualizar_estado_invalido_es_rechazado(client, admin):
    h = _h(client, admin)
    creado = _crear_equipo(client, admin)
    app_creada = client.post(f"/api/equipos/{creado['id']}/aplicaciones", json={'ejecutable': 'juego.exe'}, headers=h).get_json()
    aplicacion_id = app_creada['aplicacion']['id']

    r = client.put(
        f"/api/equipos/{creado['id']}/aplicaciones/{aplicacion_id}",
        json={'estado': 'invalido'},
        headers=h,
    )
    assert r.status_code == 400


def test_actualizar_politica_de_aplicacion_no_asignada(client, admin):
    creado = _crear_equipo(client, admin)
    r = client.put(
        f"/api/equipos/{creado['id']}/aplicaciones/999999",
        json={'estado': 'bloqueada'},
        headers=_h(client, admin),
    )
    assert r.status_code == 404


def test_quitar_aplicacion(client, admin):
    h = _h(client, admin)
    creado = _crear_equipo(client, admin)
    app_creada = client.post(f"/api/equipos/{creado['id']}/aplicaciones", json={'ejecutable': 'juego.exe'}, headers=h).get_json()
    aplicacion_id = app_creada['aplicacion']['id']

    r = client.delete(f"/api/equipos/{creado['id']}/aplicaciones/{aplicacion_id}", headers=h)
    assert r.status_code == 200
    assert EquipoAppPolitica.query.filter_by(equipo_id=creado['id'], aplicacion_id=aplicacion_id).first() is None


def test_matriz_de_control_queda_en_bitacora(client, admin):
    h = _h(client, admin)
    creado = _crear_equipo(client, admin)
    app_creada = client.post(f"/api/equipos/{creado['id']}/aplicaciones", json={'ejecutable': 'juego.exe'}, headers=h).get_json()
    client.put(
        f"/api/equipos/{creado['id']}/aplicaciones/{app_creada['aplicacion']['id']}",
        json={'estado': 'bloqueada'},
        headers=h,
    )
    bitacora = client.get('/api/bitacora?entidad=equipo', headers=h).get_json()
    assert any('juego.exe' in item['action'] or 'política' in item['action'].lower() for item in bitacora['items'])
