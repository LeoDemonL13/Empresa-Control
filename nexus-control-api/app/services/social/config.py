import os

META_GRAPH_API_VERSION = os.environ.get('META_GRAPH_API_VERSION', 'v21.0')


class ConfiguracionFaltante(Exception):
    pass


def _requerido(nombre):
    valor = os.environ.get(nombre, '').strip()
    if not valor:
        raise ConfiguracionFaltante(nombre)
    return valor


def meta_app_id():
    return _requerido('META_APP_ID')


def meta_app_secret():
    return _requerido('META_APP_SECRET')


def meta_redirect_uri():
    return _requerido('META_REDIRECT_URI')


def meta_instagram_redirect_uri():
    return _requerido('META_INSTAGRAM_REDIRECT_URI')


def tiktok_client_key():
    return _requerido('TIKTOK_CLIENT_KEY')


def tiktok_client_secret():
    return _requerido('TIKTOK_CLIENT_SECRET')


def tiktok_redirect_uri():
    return _requerido('TIKTOK_REDIRECT_URI')


def google_client_id():
    return _requerido('GOOGLE_CLIENT_ID')


def google_client_secret():
    return _requerido('GOOGLE_CLIENT_SECRET')


def google_redirect_uri():
    return _requerido('GOOGLE_REDIRECT_URI')


def redirect_uri_para(plataforma):
    if plataforma == 'facebook':
        return meta_redirect_uri()
    if plataforma == 'instagram':
        return meta_instagram_redirect_uri()
    if plataforma == 'tiktok':
        return tiktok_redirect_uri()
    if plataforma == 'youtube':
        return google_redirect_uri()
    raise ConfiguracionFaltante(plataforma)


def plataforma_configurada(plataforma):
    comprobadores = {
        'facebook': (meta_app_id, meta_app_secret, meta_redirect_uri),
        'instagram': (meta_app_id, meta_app_secret, meta_instagram_redirect_uri),
        'tiktok': (tiktok_client_key, tiktok_client_secret, tiktok_redirect_uri),
        'youtube': (google_client_id, google_client_secret, google_redirect_uri),
    }
    for fn in comprobadores.get(plataforma, ()):
        try:
            fn()
        except ConfiguracionFaltante:
            return False
    return True


def intervalo_sincronizacion_minutos():
    try:
        minutos = int(os.environ.get('SOCIAL_SYNC_INTERVAL_MINUTES', '15'))
    except ValueError:
        minutos = 15
    return max(minutos, 1)


def frontend_base_url():
    configurado = os.environ.get('FRONTEND_BASE_URL', '').strip()
    if configurado:
        return configurado.rstrip('/')
    origenes = os.environ.get('CORS_ORIGINS', 'http://localhost:5173')
    primero = [o.strip() for o in origenes.split(',') if o.strip()]
    return (primero[0] if primero else 'http://localhost:5173').rstrip('/')
