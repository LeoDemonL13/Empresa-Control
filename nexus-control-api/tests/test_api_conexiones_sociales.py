from conftest import auth_headers, login

from app.models import ConexionRedSocial
from app.services import sincronizacion_redes


def _h(client, user):
    return auth_headers(login(client, user.username).get_json()['token'])


CREDENCIALES_FACEBOOK = {'token_acceso': 'EAAtoken123', 'id_pagina': '1000200030'}


def test_requiere_sesion(client):
    r = client.get('/api/conexiones-sociales')
    assert r.status_code == 401


def test_listar_devuelve_las_plataformas_soportadas_sin_conectar(client, admin):
    r = client.get('/api/conexiones-sociales', headers=_h(client, admin))
    assert r.status_code == 200
    body = r.get_json()
    plataformas = {c['plataforma'] for c in body}
    assert plataformas == {'facebook', 'instagram', 'tiktok', 'youtube', 'x'}
    assert all(c['conectada'] is False for c in body)


def test_admin_no_puede_guardar_credenciales(client, admin):
    r = client.put('/api/conexiones-sociales/facebook', json=CREDENCIALES_FACEBOOK, headers=_h(client, admin))
    assert r.status_code == 403


def test_super_admin_guarda_credenciales_y_no_se_devuelven_en_la_respuesta(client, super_admin):
    r = client.put('/api/conexiones-sociales/facebook', json=CREDENCIALES_FACEBOOK, headers=_h(client, super_admin))
    assert r.status_code == 200
    body = r.get_json()
    assert body['conectada'] is True
    assert 'token_acceso' not in body
    assert 'credenciales_cifradas' not in body
    assert 'EAAtoken123' not in r.get_data(as_text=True)

    crudo = ConexionRedSocial.query.filter_by(plataforma='facebook').one()
    assert crudo.credenciales_cifradas == CREDENCIALES_FACEBOOK


def test_guardar_con_campo_faltante_es_rechazado(client, super_admin):
    r = client.put('/api/conexiones-sociales/facebook', json={'token_acceso': 'x'}, headers=_h(client, super_admin))
    assert r.status_code == 400


def test_guardar_plataforma_no_soportada_es_rechazado(client, super_admin):
    r = client.put('/api/conexiones-sociales/mastodon', json={'a': 'b'}, headers=_h(client, super_admin))
    assert r.status_code == 400


def test_eliminar_conexion(client, super_admin):
    client.put('/api/conexiones-sociales/facebook', json=CREDENCIALES_FACEBOOK, headers=_h(client, super_admin))
    r = client.delete('/api/conexiones-sociales/facebook', headers=_h(client, super_admin))
    assert r.status_code == 200
    assert ConexionRedSocial.query.filter_by(plataforma='facebook').count() == 0


def test_admin_no_puede_eliminar_conexion(client, admin, super_admin):
    client.put('/api/conexiones-sociales/facebook', json=CREDENCIALES_FACEBOOK, headers=_h(client, super_admin))
    r = client.delete('/api/conexiones-sociales/facebook', headers=_h(client, admin))
    assert r.status_code == 403


def test_eliminar_conexion_inexistente(client, super_admin):
    r = client.delete('/api/conexiones-sociales/youtube', headers=_h(client, super_admin))
    assert r.status_code == 404


def test_sincronizar_sin_credenciales_devuelve_502(client, admin):
    r = client.post('/api/conexiones-sociales/facebook/sincronizar', headers=_h(client, admin))
    assert r.status_code == 502
    assert r.get_json()['ok'] is False


def test_sincronizar_plataforma_exitosa(client, admin, super_admin, monkeypatch):
    client.put('/api/conexiones-sociales/facebook', json=CREDENCIALES_FACEBOOK, headers=_h(client, super_admin))
    monkeypatch.setitem(
        sincronizacion_redes.CLIENTES_POR_PLATAFORMA, 'facebook',
        lambda creds: {'me_gusta': 100, 'interacciones': 10, 'impresiones': 1000, 'engagement': 1.0},
    )

    r = client.post('/api/conexiones-sociales/facebook/sincronizar', headers=_h(client, admin))
    assert r.status_code == 200
    body = r.get_json()
    assert body['ok'] is True
    assert body['conexion']['conectada'] is True
    assert body['conexion']['ultima_sincronizacion'] is not None


def test_sincronizar_todas_las_plataformas(client, admin, super_admin, monkeypatch):
    client.put('/api/conexiones-sociales/facebook', json=CREDENCIALES_FACEBOOK, headers=_h(client, super_admin))
    client.put(
        '/api/conexiones-sociales/youtube', json={'clave_api': 'k', 'id_canal': 'c1'}, headers=_h(client, super_admin),
    )
    monkeypatch.setitem(
        sincronizacion_redes.CLIENTES_POR_PLATAFORMA, 'facebook',
        lambda creds: {'me_gusta': 1, 'interacciones': 1, 'impresiones': 10, 'engagement': 10.0},
    )
    monkeypatch.setitem(
        sincronizacion_redes.CLIENTES_POR_PLATAFORMA, 'youtube',
        lambda creds: {'me_gusta': 2, 'interacciones': 2, 'impresiones': 20, 'engagement': 10.0},
    )

    r = client.post('/api/conexiones-sociales/sincronizar-todas', headers=_h(client, admin))
    assert r.status_code == 200
    body = r.get_json()
    assert body['facebook']['ok'] is True
    assert body['youtube']['ok'] is True


def test_guardar_y_sincronizar_quedan_en_bitacora(client, admin, super_admin, monkeypatch):
    client.put('/api/conexiones-sociales/facebook', json=CREDENCIALES_FACEBOOK, headers=_h(client, super_admin))
    monkeypatch.setitem(
        sincronizacion_redes.CLIENTES_POR_PLATAFORMA, 'facebook',
        lambda creds: {'me_gusta': 1, 'interacciones': 1, 'impresiones': 10, 'engagement': 10.0},
    )
    client.post('/api/conexiones-sociales/facebook/sincronizar', headers=_h(client, admin))

    bitacora = client.get('/api/bitacora?entidad=conexion_social', headers=_h(client, super_admin)).get_json()
    acciones = [item['action'] for item in bitacora['items']]
    assert any('Guardó' in a for a in acciones)
    assert any('Sincronizó' in a for a in acciones)
