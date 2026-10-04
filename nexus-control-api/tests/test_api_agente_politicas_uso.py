from datetime import date, timedelta

from conftest import auth_headers, login

from app.models import Aplicacion, UsoAplicacion


def _h(client, user):
    return auth_headers(login(client, user.username).get_json()['token'])


def _crear_y_enrolar(client, admin, nombre='PC-Agente-Politicas'):
    h = _h(client, admin)
    creado = client.post('/api/equipos', json={'nombre': nombre}, headers=h).get_json()
    enrolado = client.post('/api/agente/enrolar', json={'codigo': creado['codigo_enrolamiento']}).get_json()
    return creado, enrolado, h


def _cabeceras_agente(enrolado):
    return {'X-Device-Id': str(enrolado['equipo_id']), 'X-Api-Key': enrolado['api_key']}


def test_obtener_politicas_sin_credenciales(client, admin):
    creado, enrolado, h = _crear_y_enrolar(client, admin)
    r = client.get('/api/agente/politicas')
    assert r.status_code == 401


def test_obtener_politicas_vacias(client, admin):
    creado, enrolado, h = _crear_y_enrolar(client, admin)
    r = client.get('/api/agente/politicas', headers=_cabeceras_agente(enrolado))
    assert r.status_code == 200
    body = r.get_json()
    assert body['politica_version'] == 1
    assert body['politicas'] == []


def test_obtener_politicas_incluye_lo_configurado_en_el_panel(client, admin):
    creado, enrolado, h = _crear_y_enrolar(client, admin)
    client.post(f"/api/equipos/{creado['id']}/aplicaciones", json={'ejecutable': 'juego.exe'}, headers=h)
    app_id = Aplicacion.query.filter_by(ejecutable_normalizado='juego.exe').one().id
    client.put(
        f"/api/equipos/{creado['id']}/aplicaciones/{app_id}",
        json={'estado': 'bloqueada'},
        headers=h,
    )

    r = client.get('/api/agente/politicas', headers=_cabeceras_agente(enrolado))
    body = r.get_json()
    assert body['politica_version'] == 2
    assert body['politicas'] == [{
        'ejecutable': 'juego.exe', 'estado': 'bloqueada', 'tipo_uso': 'sin_limite',
        'limite_minutos': None, 'periodo': 'diario',
    }]


def test_enviar_uso_sin_credenciales(client):
    r = client.post('/api/agente/uso', json={'fecha': date.today().isoformat(), 'entradas': []})
    assert r.status_code == 401


def test_enviar_uso_crea_aplicacion_y_politica_automaticamente(client, admin):
    creado, enrolado, h = _crear_y_enrolar(client, admin)
    r = client.post(
        '/api/agente/uso',
        json={'fecha': date.today().isoformat(), 'entradas': [{'ejecutable': 'notas.exe', 'segundos': 120, 'sesiones': 1}]},
        headers=_cabeceras_agente(enrolado),
    )
    assert r.status_code == 200
    aplicacion = Aplicacion.query.filter_by(ejecutable_normalizado='notas.exe').one()
    uso = UsoAplicacion.query.filter_by(equipo_id=creado['id'], aplicacion_id=aplicacion.id).one()
    assert uso.segundos == 120
    assert uso.sesiones == 1


def test_enviar_uso_acumula_en_el_mismo_dia(client, admin):
    creado, enrolado, h = _crear_y_enrolar(client, admin)
    cabeceras = _cabeceras_agente(enrolado)
    hoy = date.today().isoformat()
    client.post('/api/agente/uso', json={'fecha': hoy, 'entradas': [{'ejecutable': 'notas.exe', 'segundos': 60}]}, headers=cabeceras)
    client.post('/api/agente/uso', json={'fecha': hoy, 'entradas': [{'ejecutable': 'notas.exe', 'segundos': 30}]}, headers=cabeceras)

    aplicacion = Aplicacion.query.filter_by(ejecutable_normalizado='notas.exe').one()
    uso = UsoAplicacion.query.filter_by(equipo_id=creado['id'], aplicacion_id=aplicacion.id).one()
    assert uso.segundos == 90


def test_enviar_uso_fecha_invalida(client, admin):
    creado, enrolado, h = _crear_y_enrolar(client, admin)
    r = client.post(
        '/api/agente/uso',
        json={'fecha': 'no-es-una-fecha', 'entradas': []},
        headers=_cabeceras_agente(enrolado),
    )
    assert r.status_code == 400


def test_enviar_uso_fecha_futura_es_rechazada(client, admin):
    creado, enrolado, h = _crear_y_enrolar(client, admin)
    futura = (date.today() + timedelta(days=1)).isoformat()
    r = client.post(
        '/api/agente/uso',
        json={'fecha': futura, 'entradas': []},
        headers=_cabeceras_agente(enrolado),
    )
    assert r.status_code == 400


def test_consultar_uso_desde_el_panel(client, admin):
    creado, enrolado, h = _crear_y_enrolar(client, admin)
    client.post(
        '/api/agente/uso',
        json={'fecha': date.today().isoformat(), 'entradas': [{'ejecutable': 'notas.exe', 'segundos': 300, 'sesiones': 2}]},
        headers=_cabeceras_agente(enrolado),
    )
    r = client.get(f"/api/equipos/{creado['id']}/uso", headers=h)
    assert r.status_code == 200
    body = r.get_json()
    assert body['por_app'][0]['ejecutable'] == 'notas.exe'
    assert body['por_app'][0]['segundos'] == 300
    assert body['por_app'][0]['sesiones'] == 2
