import requests

TIEMPO_ESPERA_SEGUNDOS = 15


class ErrorSincronizacion(Exception):
    pass


def solicitar_json(metodo, url, **kwargs):
    kwargs.setdefault('timeout', TIEMPO_ESPERA_SEGUNDOS)
    try:
        respuesta = requests.request(metodo, url, **kwargs)
    except requests.RequestException as exc:
        raise ErrorSincronizacion(f'No se pudo contactar al servicio: {exc}') from exc

    try:
        cuerpo = respuesta.json()
    except ValueError:
        cuerpo = None

    if respuesta.status_code >= 400:
        detalle = None
        if isinstance(cuerpo, dict):
            error = cuerpo.get('error')
            if isinstance(error, dict):
                detalle = error.get('message')
            elif isinstance(error, str):
                detalle = error
        if not detalle:
            detalle = respuesta.text[:300]
        raise ErrorSincronizacion(f'El servicio respondió {respuesta.status_code}: {detalle}')

    if cuerpo is None:
        raise ErrorSincronizacion('El servicio devolvió una respuesta sin JSON válido')

    return cuerpo


def campo_requerido(credenciales, nombre):
    valor = (credenciales or {}).get(nombre)
    if valor is None or (isinstance(valor, str) and not valor.strip()):
        raise ErrorSincronizacion(f'Falta la credencial "{nombre}"')
    return valor.strip() if isinstance(valor, str) else valor


def calcular_engagement(interacciones, impresiones):
    if not impresiones:
        return 0.0
    return round(min((interacciones / impresiones) * 100, 100), 2)


def metricas_resultado(me_gusta=0, interacciones=0, impresiones=0, engagement=None):
    me_gusta = max(int(me_gusta or 0), 0)
    interacciones = max(int(interacciones or 0), 0)
    impresiones = max(int(impresiones or 0), 0)
    if engagement is None:
        engagement = calcular_engagement(interacciones, impresiones)
    return {
        'me_gusta': me_gusta,
        'interacciones': interacciones,
        'impresiones': impresiones,
        'engagement': engagement,
    }
