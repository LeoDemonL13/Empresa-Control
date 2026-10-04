from conftest import auth_headers, login

from app.models import MetricaSocial


def _h(client, user):
    return auth_headers(login(client, user.username).get_json()['token'])


def test_requiere_sesion(client):
    r = client.get('/api/metricas-sociales')
    assert r.status_code == 401


def test_listar_vacio(client, admin):
    r = client.get('/api/metricas-sociales', headers=_h(client, admin))
    assert r.status_code == 200
    assert r.get_json() == []


def test_guardar_crea_el_registro(client, admin):
    h = _h(client, admin)
    r = client.post(
        '/api/metricas-sociales',
        json={'red_social': 'Instagram', 'me_gusta': 1200, 'interacciones': 340, 'impresiones': 9000, 'engagement': 4.5},
        headers=h,
    )
    assert r.status_code == 201
    body = r.get_json()
    assert body['red_social'] == 'Instagram'
    assert body['me_gusta'] == 1200
    assert body['engagement'] == 4.5
    assert MetricaSocial.query.filter_by(red_social_normalizada='instagram').count() == 1


def test_guardar_actualiza_el_registro_existente_sin_duplicar(client, admin):
    h = _h(client, admin)
    client.post('/api/metricas-sociales', json={'red_social': 'Facebook', 'me_gusta': 100}, headers=h)
    r2 = client.post('/api/metricas-sociales', json={'red_social': '  facebook  ', 'me_gusta': 150}, headers=h)
    assert r2.get_json()['me_gusta'] == 150
    assert MetricaSocial.query.filter_by(red_social_normalizada='facebook').count() == 1


def test_guardar_sin_nombre_es_rechazado(client, admin):
    r = client.post('/api/metricas-sociales', json={'red_social': '  '}, headers=_h(client, admin))
    assert r.status_code == 400


def test_guardar_numero_negativo_es_rechazado(client, admin):
    r = client.post(
        '/api/metricas-sociales', json={'red_social': 'TikTok', 'me_gusta': -5}, headers=_h(client, admin),
    )
    assert r.status_code == 400


def test_guardar_engagement_fuera_de_rango_es_rechazado(client, admin):
    r = client.post(
        '/api/metricas-sociales', json={'red_social': 'TikTok', 'engagement': 150}, headers=_h(client, admin),
    )
    assert r.status_code == 400


def test_eliminar_metrica(client, admin):
    h = _h(client, admin)
    creado = client.post('/api/metricas-sociales', json={'red_social': 'X'}, headers=h).get_json()
    r = client.delete(f"/api/metricas-sociales/{creado['id']}", headers=h)
    assert r.status_code == 200
    assert MetricaSocial.query.filter_by(red_social_normalizada='x').count() == 0


def test_eliminar_metrica_inexistente(client, admin):
    r = client.delete('/api/metricas-sociales/999999', headers=_h(client, admin))
    assert r.status_code == 404


def test_guardar_metrica_queda_en_bitacora(client, admin):
    h = _h(client, admin)
    client.post('/api/metricas-sociales', json={'red_social': 'YouTube', 'me_gusta': 10}, headers=h)
    bitacora = client.get('/api/bitacora?entidad=metrica_social', headers=h).get_json()
    assert any('YouTube' in item['action'] for item in bitacora['items'])
