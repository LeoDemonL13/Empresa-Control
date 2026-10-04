from . import cache_local
from .cliente_api import ClienteAPI


def refrescar_politicas(cliente: ClienteAPI) -> dict:
    datos = cliente.obtener_politicas()
    estado = cache_local.cargar()
    estado['politica_version'] = datos['politica_version']
    estado['politicas'] = {p['ejecutable']: p for p in datos['politicas']}
    cache_local.guardar(estado)
    return estado


def enviar_uso_acumulado(cliente: ClienteAPI) -> bool:
    estado = cache_local.cargar()
    entradas = [
        {'ejecutable': ejecutable, 'segundos': segundos, 'sesiones': estado['sesiones'].get(ejecutable, 0)}
        for ejecutable, segundos in estado['acumulado'].items()
        if segundos > 0
    ]
    if not entradas:
        return False
    cliente.enviar_uso(estado['fecha'], entradas)
    return True
