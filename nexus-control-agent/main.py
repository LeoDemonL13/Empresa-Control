import argparse
import sys
import threading
import time

from agent import config, monitor_uso, registro
from agent.cliente_api import ClienteAPI, ErrorAPI
from agent.cliente_socket import crear_cliente
from agent.enrolamiento import SinCredenciales, asegurar_credenciales, enrolar
from agent.inventario import recolectar
from agent.politicas import enviar_uso_acumulado, refrescar_politicas


def _bucle_monitoreo(detener: threading.Event):
    while not detener.is_set():
        try:
            monitor_uso.aplicar_ciclo(config.INTERVALO_MONITOREO_SEGUNDOS)
        except Exception as e:
            print(f'Monitoreo: {e}')
        detener.wait(config.INTERVALO_MONITOREO_SEGUNDOS)


def _bucle_sincronia(cliente: ClienteAPI, detener: threading.Event):
    while not detener.is_set():
        detener.wait(config.INTERVALO_SINCRONIA_SEGUNDOS)
        if detener.is_set():
            break
        try:
            refrescar_politicas(cliente)
        except ErrorAPI as e:
            print(f'No se pudieron refrescar las políticas: {e}')
        try:
            enviar_uso_acumulado(cliente)
        except ErrorAPI as e:
            print(f'No se pudo enviar el uso acumulado: {e}')


def latir_seguro(latir) -> bool:
    try:
        latir()
        return True
    except Exception as e:
        print(f'No se pudo enviar la señal de vida, se reintenta: {e}')
        return False


def _leer_argumentos(argv):
    parser = argparse.ArgumentParser(description='Agente de Nexus Obsidian Control')
    parser.add_argument('--enrolar', nargs=2, metavar=('URL', 'CODIGO'), help='Enrola este equipo sin pedir datos y termina')
    parser.add_argument('--servicio', action='store_true', help='Modo desatendido: sin preguntas y con registro en archivo')
    return parser.parse_args(argv)


def main(argv=None):
    argumentos = _leer_argumentos(argv)

    if argumentos.servicio or argumentos.enrolar:
        registro.redirigir_salida()

    print(f'Nexus Obsidian Control - Agente v{config.AGENTE_VERSION}')

    if argumentos.enrolar:
        url, codigo = argumentos.enrolar
        try:
            _, _, _, nombre = enrolar(url, codigo)
        except ErrorAPI as e:
            print(f'No se pudo enrolar el equipo: {e}')
            sys.exit(1)
        print(f"Enrolado como '{nombre}'.")
        return

    try:
        equipo_id, api_key, api_base_url = asegurar_credenciales(interactivo=not argumentos.servicio)
    except SinCredenciales as e:
        print(f'{e} Ejecuta el instalador o usa --enrolar URL CODIGO.')
        sys.exit(2)
    except ErrorAPI as e:
        print(f'No se pudo enrolar el equipo: {e}')
        sys.exit(1)
    except (EOFError, KeyboardInterrupt):
        print('\nCancelado.')
        sys.exit(1)

    print(f'Servidor: {api_base_url}')
    cliente = ClienteAPI(api_base_url, equipo_id, api_key)

    try:
        cliente.enviar_inventario(recolectar())
        print('Inventario enviado.')
    except ErrorAPI as e:
        print(f'No se pudo enviar el inventario: {e}')

    try:
        refrescar_politicas(cliente)
        print('Políticas de aplicaciones sincronizadas.')
    except ErrorAPI as e:
        print(f'No se pudieron obtener las políticas: {e}')

    def al_conectar():
        print('Conectado al servidor.')

    def al_desconectar():
        print('Desconectado del servidor, reintentando...')

    def al_actualizar_politica(data):
        try:
            refrescar_politicas(cliente)
            print('Políticas actualizadas desde el panel.')
        except ErrorAPI as e:
            print(f'No se pudieron refrescar las políticas: {e}')

    sio, conectar, latir = crear_cliente(
        api_base_url, equipo_id, api_key, al_conectar, al_desconectar, al_actualizar_politica,
    )

    while True:
        try:
            conectar()
            break
        except Exception as e:
            print(f'No se pudo conectar, reintentando en 10s... ({e})')
            time.sleep(10)

    detener = threading.Event()
    hilo_monitoreo = threading.Thread(target=_bucle_monitoreo, args=(detener,), daemon=True)
    hilo_sincronia = threading.Thread(target=_bucle_sincronia, args=(cliente, detener), daemon=True)
    hilo_monitoreo.start()
    hilo_sincronia.start()

    try:
        while True:
            latir_seguro(latir)
            time.sleep(config.INTERVALO_HEARTBEAT_SEGUNDOS)
    except KeyboardInterrupt:
        print('\nDeteniendo el agente...')
        detener.set()
        sio.disconnect()


if __name__ == '__main__':
    main()
