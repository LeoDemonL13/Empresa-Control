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
    entradas = []
    for ejecutable, segundos in estado['acumulado'].items():
        enviado_previo = estado['enviado'].get(ejecutable, 0)
        delta_segundos = max(0, segundos - enviado_previo)
        sesiones = estado['sesiones'].get(ejecutable, 0)
        if delta_segundos == 0 and sesiones == 0:
            continue
        entradas.append({'ejecutable': ejecutable, 'segundos': delta_segundos, 'sesiones': sesiones})

    if not entradas:
        return False

    cliente.enviar_uso(estado['fecha'], entradas)

    for entrada in entradas:
        estado['enviado'][entrada['ejecutable']] = estado['acumulado'][entrada['ejecutable']]
        estado['sesiones'][entrada['ejecutable']] = 0
    cache_local.guardar(estado)
    return True
