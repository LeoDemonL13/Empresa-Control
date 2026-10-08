from . import almacen, config
from .cliente_api import ClienteAPI


class SinCredenciales(Exception):
    pass


def enrolar(api_base_url: str, codigo: str):
    api_base_url = api_base_url.strip().rstrip('/')
    cliente = ClienteAPI(api_base_url)
    resultado = cliente.enrolar(codigo.strip())
    almacen.guardar(resultado['equipo_id'], resultado['api_key'], api_base_url)
    return resultado['equipo_id'], resultado['api_key'], api_base_url, resultado['nombre']


def asegurar_credenciales(interactivo: bool = True):
    credenciales = almacen.cargar()
    if credenciales:
        return credenciales['equipo_id'], credenciales['api_key'], credenciales['api_base_url']

    if not interactivo:
        raise SinCredenciales('Este equipo no está enrolado todavía.')

    print('Este equipo no está enrolado todavía.')
    entrada_url = input(f'Dirección del servidor [{config.URL_POR_DEFECTO}]: ').strip()
    api_base_url = (entrada_url or config.URL_POR_DEFECTO).rstrip('/')

    codigo = input('Código de enrolamiento: ').strip()
    equipo_id, api_key, api_base_url, nombre = enrolar(api_base_url, codigo)
    print(f"Enrolado como '{nombre}'.")
    return equipo_id, api_key, api_base_url
