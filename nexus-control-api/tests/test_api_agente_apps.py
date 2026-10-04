from conftest import auth_headers, login

from app.models import AppInstalada


def _h(client, user):
    return auth_headers(login(client, user.username).get_json()['token'])


def _crear_y_enrolar(client, admin, nombre='Telefono-Recepcion', tipo='android'):
    h = _h(client, admin)
    creado = client.post('/api/equipos', json={'nombre': nombre, 'tipo': tipo}, headers=h).get_json()
    enrolado = client.post('/api/agente/enrolar', json={'codigo': creado['codigo_enrolamiento']}).get_json()
    return creado, enrolado, h


def _cabeceras_agente(enrolado):
    return {'X-Device-Id': str(enrolado['equipo_id']), 'X-Api-Key': enrolado['api_key']}


def test_enviar_apps_instaladas_sin_credenciales(client):
    r = client.post('/api/agente/apps-instaladas', json={'apps': []})
    assert r.status_code == 401


def test_enviar_apps_instaladas_las_guarda(client, admin):
    creado, enrolado, h = _crear_y_enrolar(client, admin)
    r = client.post(
        '/api/agente/apps-instaladas',
        json={'apps': [
            {'paquete': 'com.instagram.android', 'etiqueta': 'Instagram'},
            {'paquete': 'com.whatsapp', 'etiqueta': 'WhatsApp'},
        ]},
        headers=_cabeceras_agente(enrolado),
    )
    assert r.status_code == 200
    assert r.get_json()['guardadas'] == 2
    guardadas = AppInstalada.query.filter_by(equipo_id=creado['id']).order_by(AppInstalada.etiqueta).all()
    assert [a.etiqueta for a in guardadas] == ['Instagram', 'WhatsApp']


def test_enviar_apps_instaladas_reemplaza_el_inventario_anterior(client, admin):
    creado, enrolado, h = _crear_y_enrolar(client, admin)
    cabeceras = _cabeceras_agente(enrolado)
    client.post(
        '/api/agente/apps-instaladas',
        json={'apps': [{'paquete': 'com.vieja.app', 'etiqueta': 'Vieja'}]},
        headers=cabeceras,
    )
    client.post(
        '/api/agente/apps-instaladas',
        json={'apps': [{'paquete': 'com.nueva.app', 'etiqueta': 'Nueva'}]},
        headers=cabeceras,
    )
    guardadas = AppInstalada.query.filter_by(equipo_id=creado['id']).all()
    assert len(guardadas) == 1
    assert guardadas[0].paquete == 'com.nueva.app'


def test_enviar_apps_instaladas_ignora_entradas_incompletas(client, admin):
    creado, enrolado, h = _crear_y_enrolar(client, admin)
    r = client.post(
        '/api/agente/apps-instaladas',
        json={'apps': [{'paquete': 'com.ok.app', 'etiqueta': 'Ok'}, {'paquete': ''}, {'etiqueta': 'Sin paquete'}]},
        headers=_cabeceras_agente(enrolado),
    )
    assert r.status_code == 200
    assert r.get_json()['guardadas'] == 1


def test_enviar_apps_instaladas_no_es_una_lista(client, admin):
    creado, enrolado, h = _crear_y_enrolar(client, admin)
    r = client.post('/api/agente/apps-instaladas', json={'apps': 'no-es-lista'}, headers=_cabeceras_agente(enrolado))
    assert r.status_code == 400


def test_consultar_apps_instaladas_desde_el_panel(client, admin):
    creado, enrolado, h = _crear_y_enrolar(client, admin)
    client.post(
        '/api/agente/apps-instaladas',
        json={'apps': [{'paquete': 'com.whatsapp', 'etiqueta': 'WhatsApp'}]},
        headers=_cabeceras_agente(enrolado),
    )
    r = client.get(f"/api/equipos/{creado['id']}/apps-instaladas", headers=h)
    assert r.status_code == 200
    assert r.get_json() == [{'paquete': 'com.whatsapp', 'etiqueta': 'WhatsApp'}]


def test_consultar_apps_instaladas_requiere_sesion(client, admin):
    creado, enrolado, h = _crear_y_enrolar(client, admin)
    r = client.get(f"/api/equipos/{creado['id']}/apps-instaladas")
    assert r.status_code == 401


def test_consultar_apps_instaladas_equipo_inexistente(client, admin):
    h = _h(client, admin)
    r = client.get('/api/equipos/999999/apps-instaladas', headers=h)
    assert r.status_code == 404
