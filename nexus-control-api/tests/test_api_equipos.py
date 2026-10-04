from datetime import datetime, timedelta, timezone

from conftest import auth_headers, login

from app.extensions import db
from app.models import Categoria, CodigoEnrolamiento, Equipo


def _h(client, user):
    return auth_headers(login(client, user.username).get_json()['token'])


def test_requiere_sesion(client):
    r = client.get('/api/equipos')
    assert r.status_code == 401


def test_crear_equipo_minimo(client, admin):
    r = client.post('/api/equipos', json={'nombre': 'PC-Recepcion'}, headers=_h(client, admin))
    assert r.status_code == 201
    body = r.get_json()
    assert body['nombre'] == 'PC-Recepcion'
    assert body['categoria'] is None
    assert body['en_linea'] is False
    assert body['enrolado'] is False
    assert len(body['codigo_enrolamiento']) == 11
    assert body['codigo_expira_at']


def test_crear_equipo_sin_nombre(client, admin):
    r = client.post('/api/equipos', json={'nombre': '  '}, headers=_h(client, admin))
    assert r.status_code == 400


def test_crear_equipo_con_categoria_nueva_la_autocrea(client, admin):
    r = client.post('/api/equipos', json={'nombre': 'PC-01', 'categoria': 'Ventas'}, headers=_h(client, admin))
    assert r.status_code == 201
    assert r.get_json()['categoria']['nombre'] == 'Ventas'
    assert Categoria.query.filter_by(nombre_normalizado='ventas').count() == 1


def test_crear_equipo_con_categoria_existente_reutiliza_sin_duplicar(client, admin):
    h = _h(client, admin)
    client.post('/api/equipos', json={'nombre': 'PC-01', 'categoria': 'Ventas'}, headers=h)
    r2 = client.post('/api/equipos', json={'nombre': 'PC-02', 'categoria': '  ventas  '}, headers=h)
    assert r2.status_code == 201
    assert Categoria.query.filter_by(nombre_normalizado='ventas').count() == 1
    assert r2.get_json()['categoria']['nombre'] == 'Ventas'


def test_listar_equipos_filtra_por_categoria(client, admin):
    h = _h(client, admin)
    client.post('/api/equipos', json={'nombre': 'PC-Ventas-1', 'categoria': 'Ventas'}, headers=h)
    client.post('/api/equipos', json={'nombre': 'PC-Soporte-1', 'categoria': 'Soporte'}, headers=h)
    ventas_id = Categoria.query.filter_by(nombre_normalizado='ventas').first().id

    r = client.get(f'/api/equipos?categoria_id={ventas_id}', headers=h)
    nombres = [e['nombre'] for e in r.get_json()]
    assert nombres == ['PC-Ventas-1']


def test_listar_equipos_filtra_por_busqueda(client, admin):
    h = _h(client, admin)
    client.post('/api/equipos', json={'nombre': 'PC-Gerencia', 'usuario_asignado': 'Leo'}, headers=h)
    client.post('/api/equipos', json={'nombre': 'PC-Bodega', 'usuario_asignado': 'Ana'}, headers=h)

    r = client.get('/api/equipos?q=leo', headers=h)
    nombres = [e['nombre'] for e in r.get_json()]
    assert nombres == ['PC-Gerencia']


def test_listar_equipos_filtra_por_estado(client, admin, app):
    h = _h(client, admin)
    client.post('/api/equipos', json={'nombre': 'PC-en-linea'}, headers=h)
    client.post('/api/equipos', json={'nombre': 'PC-fuera'}, headers=h)

    en_linea = Equipo.query.filter_by(nombre='PC-en-linea').one()
    en_linea.ultimo_latido = datetime.now(timezone.utc)
    fuera = Equipo.query.filter_by(nombre='PC-fuera').one()
    fuera.ultimo_latido = datetime.now(timezone.utc) - timedelta(minutes=10)
    db.session.commit()

    r_en = client.get('/api/equipos?estado=en_linea', headers=h)
    assert [e['nombre'] for e in r_en.get_json()] == ['PC-en-linea']

    r_fuera = client.get('/api/equipos?estado=fuera_linea', headers=h)
    assert 'PC-fuera' in [e['nombre'] for e in r_fuera.get_json()]
    assert 'PC-en-linea' not in [e['nombre'] for e in r_fuera.get_json()]


def test_detalle_incluye_codigo_pendiente(client, admin):
    h = _h(client, admin)
    creado = client.post('/api/equipos', json={'nombre': 'PC-Detalle'}, headers=h).get_json()
    r = client.get(f"/api/equipos/{creado['id']}", headers=h)
    assert r.get_json()['codigo_pendiente'] is not None


def test_detalle_no_incluye_codigo_expirado(client, admin, app):
    h = _h(client, admin)
    creado = client.post('/api/equipos', json={'nombre': 'PC-Expira'}, headers=h).get_json()
    codigo = CodigoEnrolamiento.query.filter_by(equipo_id=creado['id']).one()
    codigo.expira_at = datetime.now(timezone.utc) - timedelta(minutes=1)
    db.session.commit()
    r = client.get(f"/api/equipos/{creado['id']}", headers=h)
    assert r.get_json()['codigo_pendiente'] is None


def test_detalle_de_equipo_inexistente(client, admin):
    r = client.get('/api/equipos/999999', headers=_h(client, admin))
    assert r.status_code == 404


def test_actualizar_equipo_cambia_categoria(client, admin):
    h = _h(client, admin)
    creado = client.post('/api/equipos', json={'nombre': 'PC-Mov', 'categoria': 'Ventas'}, headers=h).get_json()
    r = client.put(f"/api/equipos/{creado['id']}", json={'categoria': 'Soporte'}, headers=h)
    assert r.status_code == 200
    assert r.get_json()['categoria']['nombre'] == 'Soporte'


def test_actualizar_equipo_quita_categoria(client, admin):
    h = _h(client, admin)
    creado = client.post('/api/equipos', json={'nombre': 'PC-Sin-Cat', 'categoria': 'Ventas'}, headers=h).get_json()
    r = client.put(f"/api/equipos/{creado['id']}", json={'categoria': ''}, headers=h)
    assert r.get_json()['categoria'] is None


def test_actualizar_equipo_nombre_vacio_rechazado(client, admin):
    h = _h(client, admin)
    creado = client.post('/api/equipos', json={'nombre': 'PC-X'}, headers=h).get_json()
    r = client.put(f"/api/equipos/{creado['id']}", json={'nombre': '  '}, headers=h)
    assert r.status_code == 400


def test_eliminar_equipo_es_baja_logica(client, admin):
    h = _h(client, admin)
    creado = client.post('/api/equipos', json={'nombre': 'PC-Baja'}, headers=h).get_json()
    r = client.delete(f"/api/equipos/{creado['id']}", headers=h)
    assert r.status_code == 200
    assert db.session.get(Equipo, creado['id']).activo is False
    assert creado['nombre'] not in [e['nombre'] for e in client.get('/api/equipos', headers=h).get_json()]


def test_regenerar_codigo_invalida_el_anterior(client, admin):
    h = _h(client, admin)
    creado = client.post('/api/equipos', json={'nombre': 'PC-Codigo'}, headers=h).get_json()
    primero = CodigoEnrolamiento.query.filter_by(equipo_id=creado['id']).one()

    r = client.post(f"/api/equipos/{creado['id']}/enrolamiento", headers=h)
    assert r.status_code == 200
    nuevo_codigo = r.get_json()['codigo_enrolamiento']
    assert nuevo_codigo != creado['codigo_enrolamiento']

    db.session.refresh(primero)
    expira = primero.expira_at
    if expira.tzinfo is None:
        expira = expira.replace(tzinfo=timezone.utc)
    assert expira <= datetime.now(timezone.utc)

    detalle = client.get(f"/api/equipos/{creado['id']}", headers=h).get_json()
    assert detalle['codigo_pendiente'] is not None


def test_creacion_de_equipo_queda_en_bitacora(client, admin):
    h = _h(client, admin)
    client.post('/api/equipos', json={'nombre': 'PC-Auditada'}, headers=h)
    bitacora = client.get('/api/bitacora?entidad=equipo', headers=h).get_json()
    assert any('PC-Auditada' in item['action'] for item in bitacora['items'])
