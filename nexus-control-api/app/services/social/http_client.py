import requests

from app.services.social.errors import SocialProviderError

TIEMPO_ESPERA_SEGUNDOS = 20


def _clasificar_status(status_code, clasificar_extra, cuerpo):
    if clasificar_extra:
        tipo = clasificar_extra(status_code, cuerpo)
        if tipo:
            return tipo
    if status_code == 429:
        return 'limite_tasa'
    if status_code == 401:
        return 'token_expirado'
    if status_code == 403:
        return 'permisos_revocados'
    if status_code == 404:
        return 'cuenta_eliminada'
    if status_code >= 500:
        return 'servidor_caido'
    return 'desconocido'


def solicitar(metodo, url, clasificar_extra=None, **kwargs):
    kwargs.setdefault('timeout', TIEMPO_ESPERA_SEGUNDOS)
    try:
        respuesta = requests.request(metodo, url, **kwargs)
    except requests.Timeout as exc:
        raise SocialProviderError('timeout', 'La plataforma no respondió a tiempo', str(exc)) from exc
    except requests.ConnectionError as exc:
        raise SocialProviderError('servidor_caido', 'No se pudo contactar a la plataforma', str(exc)) from exc
    except requests.RequestException as exc:
        raise SocialProviderError('desconocido', 'Error de red al contactar a la plataforma', str(exc)) from exc

    try:
        cuerpo = respuesta.json()
    except ValueError:
        cuerpo = None

    if respuesta.status_code >= 400:
        tipo = _clasificar_status(respuesta.status_code, clasificar_extra, cuerpo)
        detalle = None
        if isinstance(cuerpo, dict):
            detalle = str(cuerpo)[:2000]
        if not detalle:
            detalle = respuesta.text[:2000]
        retry_after = respuesta.headers.get('Retry-After')
        try:
            retry_after = int(retry_after) if retry_after else None
        except ValueError:
            retry_after = None
        raise SocialProviderError(
            tipo, f'La plataforma respondió con error {respuesta.status_code}', detalle, retry_after,
        )

    if cuerpo is None:
        raise SocialProviderError('desconocido', 'La plataforma devolvió una respuesta sin JSON válido')

    return cuerpo
