from . import almacen, config
from .cliente_api import ClienteAPI


def asegurar_credenciales():
    credenciales = almacen.cargar()
    if credenciales:
        return credenciales['equipo_id'], credenciales['api_key'], credenciales['api_base_url']

    print('Este equipo no está enrolado todavía.')
    entrada_url = input(f'Dirección del servidor [{config.URL_POR_DEFECTO}]: ').strip()
    api_base_url = (entrada_url or config.URL_POR_DEFECTO).rstrip('/')

    codigo = input('Código de enrolamiento: ').strip()
    cliente = ClienteAPI(api_base_url)
    resultado = cliente.enrolar(codigo)

    almacen.guardar(resultado['equipo_id'], resultado['api_key'], api_base_url)
    print(f"Enrolado como '{resultado['nombre']}'.")
    return resultado['equipo_id'], resultado['api_key'], api_base_url
