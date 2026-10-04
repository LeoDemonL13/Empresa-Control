from datetime import date, datetime, timedelta, timezone

from conftest import auth_headers, login

from app.extensions import db
from app.models import Equipo


def _h(client, user):
    return auth_headers(login(client, user.username).get_json()['token'])


def test_requiere_sesion(client):
    r = client.get('/api/dashboard/resumen')
    assert r.status_code == 401


def test_resumen_vacio(client, admin):
    r = client.get('/api/dashboard/resumen', headers=_h(client, admin))
    assert r.status_code == 200
    body = r.get_json()
    assert body['equipos_registrados'] == 0
    assert body['en_linea'] == 0
    assert body['fuera_linea'] == 0
    assert body['apps_bloqueadas'] == 0
    assert body['top_aplicaciones'] == []


def test_resumen_cuenta_equipos_en_linea_y_fuera_de_linea(client, admin):
    h = _h(client, admin)
    client.post('/api/equipos', json={'nombre': 'PC-En-Linea'}, headers=h)
    client.post('/api/equipos', json={'nombre': 'PC-Fuera'}, headers=h)

    en_linea = Equipo.query.filter_by(nombre='PC-En-Linea').one()
    en_linea.ultimo_latido = datetime.now(timezone.utc)
    fuera = Equipo.query.filter_by(nombre='PC-Fuera').one()
    fuera.ultimo_latido = datetime.now(timezone.utc) - timedelta(minutes=10)
    db.session.commit()

    r = client.get('/api/dashboard/resumen', headers=h)
    body = r.get_json()
    assert body['equipos_registrados'] == 2
    assert body['en_linea'] == 1
    assert body['fuera_linea'] == 1


def test_resumen_cuenta_apps_bloqueadas(client, admin):
    h = _h(client, admin)
    creado = client.post('/api/equipos', json={'nombre': 'PC-Bloqueos'}, headers=h).get_json()
    app1 = client.post(f"/api/equipos/{creado['id']}/aplicaciones", json={'ejecutable': 'juego.exe'}, headers=h).get_json()
    client.post(f"/api/equipos/{creado['id']}/aplicaciones", json={'ejecutable': 'oficina.exe'}, headers=h)
    client.put(
        f"/api/equipos/{creado['id']}/aplicaciones/{app1['aplicacion']['id']}",
        json={'estado': 'bloqueada'}, headers=h,
    )

    r = client.get('/api/dashboard/resumen', headers=h)
    assert r.get_json()['apps_bloqueadas'] == 1


def test_resumen_equipo_dado_de_baja_no_cuenta(client, admin):
    h = _h(client, admin)
    creado = client.post('/api/equipos', json={'nombre': 'PC-Baja'}, headers=h).get_json()
    client.delete(f"/api/equipos/{creado['id']}", headers=h)

    r = client.get('/api/dashboard/resumen', headers=h)
    assert r.get_json()['equipos_registrados'] == 0


def test_resumen_top_aplicaciones_ordenadas_por_uso(client, admin):
    h = _h(client, admin)
    creado = client.post('/api/equipos', json={'nombre': 'PC-Uso'}, headers=h).get_json()
    enrolado = client.post('/api/agente/enrolar', json={'codigo': creado['codigo_enrolamiento']}).get_json()
    cabeceras = {'X-Device-Id': str(enrolado['equipo_id']), 'X-Api-Key': enrolado['api_key']}

    hoy = date.today().isoformat()
    client.post('/api/agente/uso', json={'fecha': hoy, 'entradas': [{'ejecutable': 'chrome.exe', 'segundos': 300}]}, headers=cabeceras)
    client.post('/api/agente/uso', json={'fecha': hoy, 'entradas': [{'ejecutable': 'notas.exe', 'segundos': 60}]}, headers=cabeceras)

    r = client.get('/api/dashboard/resumen', headers=h)
    top = r.get_json()['top_aplicaciones']
    assert top[0]['ejecutable'] == 'chrome.exe'
    assert top[0]['segundos'] == 300
