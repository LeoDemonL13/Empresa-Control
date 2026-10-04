import socketio

from . import config


def crear_cliente(
    api_base_url: str, equipo_id: int, api_key: str,
    on_conectado=None, on_desconectado=None, on_politica_actualizada=None,
):
    sio = socketio.Client(reconnection=True, reconnection_delay=3, reconnection_delay_max=30)

    @sio.event(namespace='/agent')
    def connect():
        if on_conectado:
            on_conectado()

    @sio.event(namespace='/agent')
    def disconnect():
        if on_desconectado:
            on_desconectado()

    @sio.on('politica:actualizar', namespace='/agent')
    def _on_politica_actualizar(data=None):
        if on_politica_actualizada:
            on_politica_actualizada(data or {})

    def conectar():
        sio.connect(
            api_base_url,
            namespaces=['/agent'],
            auth={'device_id': equipo_id, 'api_key': api_key},
            wait_timeout=10,
        )

    def latir():
        sio.emit('heartbeat', {}, namespace='/agent')

    return sio, conectar, latir
