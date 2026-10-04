from datetime import datetime, timedelta, timezone

from conftest import auth_headers, login

from app.extensions import db
from app.models import CodigoEnrolamiento, Equipo


def _h(client, user):
    return auth_headers(login(client, user.username).get_json()['token'])


def _crear_equipo(client, admin, nombre='PC-Agente'):
    return client.post('/api/equipos', json={'nombre': nombre}, headers=_h(client, admin)).get_json()


def test_enrolar_con_codigo_valido(client, admin):
    creado = _crear_equipo(client, admin)
    r = client.post('/api/agente/enrolar', json={'codigo': creado['codigo_enrolamiento']})
    assert r.status_code == 200
    body = r.get_json()
    assert body['equipo_id'] == creado['id']
    assert body['nombre'] == creado['nombre']
    assert len(body['api_key']) > 20

    equipo = db.session.get(Equipo, creado['id'])
    assert equipo.api_key_hash is not None
    assert equipo.api_key_prefijo == body['api_key'][:8]


def test_enrolar_minuscula_tambien_funciona(client, admin):
    creado = _crear_equipo(client, admin)
    r = client.post('/api/agente/enrolar', json={'codigo': creado['codigo_enrolamiento'].lower()})
    assert r.status_code == 200


def test_enrolar_codigo_inexistente(client):
    r = client.post('/api/agente/enrolar', json={'codigo': 'ZZZZZ-ZZZZZ'})
    assert r.status_code == 400


def test_enrolar_codigo_vacio(client):
    r = client.post('/api/agente/enrolar', json={'codigo': ''})
    assert r.status_code == 400


def test_enrolar_codigo_ya_usado_no_se_puede_reutilizar(client, admin):
    creado = _crear_equipo(client, admin)
    primero = client.post('/api/agente/enrolar', json={'codigo': creado['codigo_enrolamiento']})
    assert primero.status_code == 200
    segundo = client.post('/api/agente/enrolar', json={'codigo': creado['codigo_enrolamiento']})
    assert segundo.status_code == 400


def test_enrolar_codigo_expirado(client, admin):
    creado = _crear_equipo(client, admin)
    registro = CodigoEnrolamiento.query.filter_by(equipo_id=creado['id']).one()
    registro.expira_at = datetime.now(timezone.utc) - timedelta(minutes=1)
    db.session.commit()
    r = client.post('/api/agente/enrolar', json={'codigo': creado['codigo_enrolamiento']})
    assert r.status_code == 400


def test_enrolar_equipo_dado_de_baja(client, admin):
    creado = _crear_equipo(client, admin)
    client.delete(f"/api/equipos/{creado['id']}", headers=_h(client, admin))
    r = client.post('/api/agente/enrolar', json={'codigo': creado['codigo_enrolamiento']})
    assert r.status_code == 400


def test_inventario_requiere_credenciales(client, admin):
    creado = _crear_equipo(client, admin)
    r = client.post('/api/agente/inventario', json={'hostname': 'PC-X'})
    assert r.status_code == 401


def test_inventario_con_api_key_invalida(client, admin):
    creado = _crear_equipo(client, admin)
    client.post('/api/agente/enrolar', json={'codigo': creado['codigo_enrolamiento']})
    r = client.post(
        '/api/agente/inventario',
        json={'hostname': 'PC-X'},
        headers={'X-Device-Id': str(creado['id']), 'X-Api-Key': 'clave-falsa'},
    )
    assert r.status_code == 401


def test_inventario_actualiza_datos_del_equipo(client, admin):
    creado = _crear_equipo(client, admin)
    enrolado = client.post('/api/agente/enrolar', json={'codigo': creado['codigo_enrolamiento']}).get_json()

    r = client.post(
        '/api/agente/inventario',
        json={
            'hostname': 'PC-AGENTE-01',
            'ip': '192.168.1.50',
            'mac': 'AA:BB:CC:DD:EE:01',
            'sistema_operativo': 'Windows 11 Pro',
            'agente_version': '0.1.0',
        },
        headers={'X-Device-Id': str(enrolado['equipo_id']), 'X-Api-Key': enrolado['api_key']},
    )
    assert r.status_code == 200

    equipo = db.session.get(Equipo, creado['id'])
    assert equipo.hostname == 'PC-AGENTE-01'
    assert equipo.mac == 'AA:BB:CC:DD:EE:01'
    assert equipo.ultimo_latido is not None


def test_inventario_mac_duplicada_es_rechazada(client, admin):
    e1 = _crear_equipo(client, admin, 'PC-Uno')
    e2 = _crear_equipo(client, admin, 'PC-Dos')
    a1 = client.post('/api/agente/enrolar', json={'codigo': e1['codigo_enrolamiento']}).get_json()
    a2 = client.post('/api/agente/enrolar', json={'codigo': e2['codigo_enrolamiento']}).get_json()

    client.post(
        '/api/agente/inventario',
        json={'mac': 'AA:AA:AA:AA:AA:AA'},
        headers={'X-Device-Id': str(a1['equipo_id']), 'X-Api-Key': a1['api_key']},
    )
    r = client.post(
        '/api/agente/inventario',
        json={'mac': 'AA:AA:AA:AA:AA:AA'},
        headers={'X-Device-Id': str(a2['equipo_id']), 'X-Api-Key': a2['api_key']},
    )
    assert r.status_code == 409


def test_inventario_de_equipo_desactivado_es_rechazado(client, admin):
    creado = _crear_equipo(client, admin)
    enrolado = client.post('/api/agente/enrolar', json={'codigo': creado['codigo_enrolamiento']}).get_json()
    client.delete(f"/api/equipos/{creado['id']}", headers=_h(client, admin))
    r = client.post(
        '/api/agente/inventario',
        json={'hostname': 'x'},
        headers={'X-Device-Id': str(enrolado['equipo_id']), 'X-Api-Key': enrolado['api_key']},
    )
    assert r.status_code == 401


def test_enrolamiento_queda_en_bitacora_con_origen_agente(client, admin):
    creado = _crear_equipo(client, admin)
    client.post('/api/agente/enrolar', json={'codigo': creado['codigo_enrolamiento']})
    bitacora = client.get('/api/bitacora?origen=agente', headers=_h(client, admin)).get_json()
    assert len(bitacora['items']) == 1
    assert 'enrolamiento' in bitacora['items'][0]['action']
