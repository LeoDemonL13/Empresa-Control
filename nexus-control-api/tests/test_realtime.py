from conftest import auth_headers, login

from app.extensions import db
from app.realtime import socketio


def _token(client, user):
    return login(client, user.username).get_json()['token']


def test_conexion_socket_sin_token_es_rechazada(app):
    sio = socketio.test_client(app, namespace='/')
    assert sio.is_connected('/') is False


def test_conexion_socket_con_token_valido(app, client, admin):
    token = _token(client, admin)
    sio = socketio.test_client(app, namespace='/', auth={'token': token})
    assert sio.is_connected('/') is True
    sio.disconnect()


def test_conexion_socket_con_token_revocado_es_rechazada(app, client, admin):
    token = _token(client, admin)
    admin.password_version = (admin.password_version or 1) + 1
    db.session.commit()
    sio = socketio.test_client(app, namespace='/', auth={'token': token})
    assert sio.is_connected('/') is False


def test_bitacora_nuevo_llega_por_socket_a_administradores(app, client, admin):
    token = _token(client, admin)
    sio = socketio.test_client(app, namespace='/', auth={'token': token})
    sio.get_received()

    from app.utils import log_action
    with app.test_request_context('/'):
        log_action('acción visible en vivo')

    recibidos = sio.get_received()
    nombres = [r['name'] for r in recibidos]
    assert 'bitacora:nuevo' in nombres
    sio.disconnect()


def test_force_logout_desconecta_al_usuario(app, client, admin):
    from app.realtime import force_logout_user

    token = _token(client, admin)
    sio = socketio.test_client(app, namespace='/', auth={'token': token})
    assert sio.is_connected('/') is True
    force_logout_user(admin.id)
    assert sio.is_connected('/') is False


def test_equipo_alta_llega_por_socket(app, client, admin):
    token = _token(client, admin)
    sio = socketio.test_client(app, namespace='/', auth={'token': token})
    sio.get_received()

    client.post('/api/equipos', json={'nombre': 'PC-Socket'}, headers={'Authorization': f'Bearer {token}'})

    recibidos = sio.get_received()
    nombres = [r['name'] for r in recibidos]
    assert 'equipo:alta' in nombres
    sio.disconnect()


def test_categoria_nueva_llega_por_socket(app, client, admin):
    token = _token(client, admin)
    sio = socketio.test_client(app, namespace='/', auth={'token': token})
    sio.get_received()

    client.post(
        '/api/equipos',
        json={'nombre': 'PC-Socket-2', 'categoria': 'Marketing'},
        headers={'Authorization': f'Bearer {token}'},
    )

    recibidos = sio.get_received()
    nombres = [r['name'] for r in recibidos]
    assert 'categoria:nueva' in nombres
    sio.disconnect()


def _enrolar_equipo(client, admin, nombre='PC-Socket-Agente'):
    h = auth_headers(login(client, admin.username).get_json()['token'])
    creado = client.post('/api/equipos', json={'nombre': nombre}, headers=h).get_json()
    return client.post('/api/agente/enrolar', json={'codigo': creado['codigo_enrolamiento']}).get_json()


def test_agente_conecta_con_credenciales_validas(app, client, admin):
    enrolado = _enrolar_equipo(client, admin)
    sio = socketio.test_client(
        app, namespace='/agent', auth={'device_id': enrolado['equipo_id'], 'api_key': enrolado['api_key']},
    )
    assert sio.is_connected('/agent') is True
    sio.disconnect(namespace='/agent')


def test_agente_rechazado_con_api_key_invalida(app, client, admin):
    enrolado = _enrolar_equipo(client, admin)
    sio = socketio.test_client(
        app, namespace='/agent', auth={'device_id': enrolado['equipo_id'], 'api_key': 'incorrecta'},
    )
    assert sio.is_connected('/agent') is False


def test_agente_rechazado_sin_device_id(app):
    sio = socketio.test_client(app, namespace='/agent', auth={'api_key': 'x'})
    assert sio.is_connected('/agent') is False


def test_heartbeat_actualiza_ultimo_latido_y_avisa_a_admins(app, client, admin):
    from app.extensions import db
    from app.models import Equipo

    enrolado = _enrolar_equipo(client, admin)
    admin_token = _token(client, admin)
    sio_admin = socketio.test_client(app, namespace='/', auth={'token': admin_token})
    sio_admin.get_received()

    sio_agente = socketio.test_client(
        app, namespace='/agent', auth={'device_id': enrolado['equipo_id'], 'api_key': enrolado['api_key']},
    )
    sio_agente.emit('heartbeat', {}, namespace='/agent')

    equipo = db.session.get(Equipo, enrolado['equipo_id'])
    assert equipo.ultimo_latido is not None

    recibidos = sio_admin.get_received()
    assert any(r['name'] == 'equipo:estado' for r in recibidos)
    sio_agente.disconnect(namespace='/agent')
    sio_admin.disconnect()


def test_heartbeat_repetido_no_reemite_si_ya_estaba_en_linea(app, client, admin):
    enrolado = _enrolar_equipo(client, admin)
    admin_token = _token(client, admin)
    sio_admin = socketio.test_client(app, namespace='/', auth={'token': admin_token})

    sio_agente = socketio.test_client(
        app, namespace='/agent', auth={'device_id': enrolado['equipo_id'], 'api_key': enrolado['api_key']},
    )
    sio_agente.emit('heartbeat', {}, namespace='/agent')
    sio_admin.get_received()

    sio_agente.emit('heartbeat', {}, namespace='/agent')
    recibidos = sio_admin.get_received()
    assert not any(r['name'] == 'equipo:estado' for r in recibidos)
    sio_agente.disconnect(namespace='/agent')
    sio_admin.disconnect()


def test_revisar_estado_equipos_detecta_transicion_a_fuera_de_linea(app, client, admin):
    from datetime import datetime, timedelta, timezone

    from app.extensions import db
    from app.models import Equipo
    from app.realtime import _estado_conocido, _revisar_estado_equipos

    enrolado = _enrolar_equipo(client, admin)
    admin_token = _token(client, admin)
    sio_admin = socketio.test_client(app, namespace='/', auth={'token': admin_token})

    sio_agente = socketio.test_client(
        app, namespace='/agent', auth={'device_id': enrolado['equipo_id'], 'api_key': enrolado['api_key']},
    )
    sio_agente.emit('heartbeat', {}, namespace='/agent')
    sio_admin.get_received()

    equipo = db.session.get(Equipo, enrolado['equipo_id'])
    equipo.ultimo_latido = datetime.now(timezone.utc) - timedelta(minutes=5)
    db.session.commit()

    _estado_conocido.clear()
    _estado_conocido[equipo.id] = True
    _revisar_estado_equipos()

    recibidos = sio_admin.get_received()
    assert any(r['name'] == 'equipo:estado' and r['args'][0]['id'] == equipo.id for r in recibidos)
    assert _estado_conocido[equipo.id] is False
    sio_agente.disconnect(namespace='/agent')
    sio_admin.disconnect()


def test_politica_actualizar_llega_al_agente_conectado(app, client, admin):
    enrolado = _enrolar_equipo(client, admin)
    h = auth_headers(login(client, admin.username).get_json()['token'])

    sio_agente = socketio.test_client(
        app, namespace='/agent', auth={'device_id': enrolado['equipo_id'], 'api_key': enrolado['api_key']},
    )
    sio_agente.get_received(namespace='/agent')

    client.post(
        f"/api/equipos/{enrolado['equipo_id']}/aplicaciones",
        json={'ejecutable': 'juego.exe'},
        headers=h,
    )
    from app.models import Aplicacion
    aplicacion_id = Aplicacion.query.filter_by(ejecutable_normalizado='juego.exe').one().id
    client.put(
        f"/api/equipos/{enrolado['equipo_id']}/aplicaciones/{aplicacion_id}",
        json={'estado': 'bloqueada'},
        headers=h,
    )

    recibidos = sio_agente.get_received(namespace='/agent')
    nombres = [r['name'] for r in recibidos]
    assert 'politica:actualizar' in nombres
    sio_agente.disconnect(namespace='/agent')
