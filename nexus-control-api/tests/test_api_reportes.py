from datetime import date

from conftest import auth_headers, login


def _h(client, user):
    return auth_headers(login(client, user.username).get_json()['token'])


def test_requiere_sesion(client):
    r = client.get('/api/reportes/general')
    assert r.status_code == 401


def test_general_pdf_por_defecto(client, admin):
    r = client.get('/api/reportes/general', headers=_h(client, admin))
    assert r.status_code == 200
    assert r.mimetype == 'application/pdf'
    assert 'attachment' in r.headers['Content-Disposition']
    assert len(r.data) > 100


def test_general_formato_invalido(client, admin):
    r = client.get('/api/reportes/general?formato=doc', headers=_h(client, admin))
    assert r.status_code == 400


def test_general_csv_incluye_los_equipos(client, admin):
    h = _h(client, admin)
    client.post('/api/equipos', json={'nombre': 'PC-Reporte-General'}, headers=h)
    r = client.get('/api/reportes/general?formato=csv', headers=h)
    assert r.status_code == 200
    assert r.mimetype == 'text/csv'
    assert 'PC-Reporte-General' in r.data.decode('utf-8-sig')


def test_general_xlsx_se_genera(client, admin):
    r = client.get('/api/reportes/general?formato=xlsx', headers=_h(client, admin))
    assert r.status_code == 200
    assert r.mimetype == 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    assert r.data[:2] == b'PK'


def test_uso_fechas_invalidas(client, admin):
    r = client.get('/api/reportes/uso?desde=no-es-fecha', headers=_h(client, admin))
    assert r.status_code == 400


def test_uso_rango_invertido(client, admin):
    r = client.get('/api/reportes/uso?desde=2026-10-10&hasta=2026-10-01', headers=_h(client, admin))
    assert r.status_code == 400


def test_uso_csv_incluye_datos_reportados_por_el_agente(client, admin):
    h = _h(client, admin)
    creado = client.post('/api/equipos', json={'nombre': 'PC-Reporte-Uso'}, headers=h).get_json()
    enrolado = client.post('/api/agente/enrolar', json={'codigo': creado['codigo_enrolamiento']}).get_json()
    cabeceras = {'X-Device-Id': str(enrolado['equipo_id']), 'X-Api-Key': enrolado['api_key']}
    client.post(
        '/api/agente/uso',
        json={'fecha': date.today().isoformat(), 'entradas': [{'ejecutable': 'chrome.exe', 'segundos': 120}]},
        headers=cabeceras,
    )

    r = client.get('/api/reportes/uso?formato=csv', headers=h)
    texto = r.data.decode('utf-8-sig')
    assert 'PC-Reporte-Uso' in texto
    assert 'chrome.exe' in texto


def test_uso_filtra_por_equipo(client, admin):
    h = _h(client, admin)
    e1 = client.post('/api/equipos', json={'nombre': 'PC-Filtro-1'}, headers=h).get_json()
    e2 = client.post('/api/equipos', json={'nombre': 'PC-Filtro-2'}, headers=h).get_json()
    a1 = client.post('/api/agente/enrolar', json={'codigo': e1['codigo_enrolamiento']}).get_json()
    a2 = client.post('/api/agente/enrolar', json={'codigo': e2['codigo_enrolamiento']}).get_json()
    hoy = date.today().isoformat()
    client.post(
        '/api/agente/uso', json={'fecha': hoy, 'entradas': [{'ejecutable': 'a.exe', 'segundos': 60}]},
        headers={'X-Device-Id': str(a1['equipo_id']), 'X-Api-Key': a1['api_key']},
    )
    client.post(
        '/api/agente/uso', json={'fecha': hoy, 'entradas': [{'ejecutable': 'b.exe', 'segundos': 60}]},
        headers={'X-Device-Id': str(a2['equipo_id']), 'X-Api-Key': a2['api_key']},
    )

    r = client.get(f"/api/reportes/uso?formato=csv&equipo_id={a1['equipo_id']}", headers=h)
    texto = r.data.decode('utf-8-sig')
    assert 'PC-Filtro-1' in texto
    assert 'PC-Filtro-2' not in texto


def test_auditoria_csv_incluye_acciones_recientes(client, admin):
    h = _h(client, admin)
    client.post('/api/equipos', json={'nombre': 'PC-Auditoria-Reporte'}, headers=h)
    r = client.get('/api/reportes/auditoria?formato=csv', headers=h)
    assert r.status_code == 200
    assert 'PC-Auditoria-Reporte' in r.data.decode('utf-8-sig')


def test_auditoria_filtra_por_origen(client, admin):
    h = _h(client, admin)
    creado = client.post('/api/equipos', json={'nombre': 'PC-Origen'}, headers=h).get_json()
    client.post('/api/agente/enrolar', json={'codigo': creado['codigo_enrolamiento']})

    r = client.get('/api/reportes/auditoria?formato=csv&origen=agente', headers=h)
    texto = r.data.decode('utf-8-sig')
    assert 'enrolamiento' in texto.lower()


def test_generar_reporte_queda_en_bitacora(client, admin):
    h = _h(client, admin)
    client.get('/api/reportes/general', headers=h)
    bitacora = client.get('/api/bitacora?entidad=reporte', headers=h).get_json()
    assert any('reporte general' in item['action'].lower() for item in bitacora['items'])
