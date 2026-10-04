import urllib.parse

from app.services.social import config
from app.services.social.errors import SocialProviderError
from app.services.social.http_client import solicitar
from app.services.social.providers.base import SocialProvider

ALCANCE_YOUTUBE = 'https://www.googleapis.com/auth/youtube.readonly'


def _clasificar_google(status_code, cuerpo):
    if not isinstance(cuerpo, dict):
        return None
    error = cuerpo.get('error')
    if isinstance(error, str):
        if error == 'invalid_grant':
            return 'refresh_expirado'
        return None
    if isinstance(error, dict):
        estado = error.get('status')
        if estado == 'PERMISSION_DENIED':
            return 'permisos_revocados'
        if estado == 'RESOURCE_EXHAUSTED':
            return 'limite_tasa'
        for e in error.get('errors') or []:
            razon = e.get('reason', '')
            if razon in ('quotaExceeded', 'rateLimitExceeded', 'userRateLimitExceeded'):
                return 'limite_tasa'
            if razon == 'accessNotConfigured':
                return 'api_deshabilitada'
            if razon in ('authError', 'insufficientPermissions'):
                return 'permisos_revocados'
    return None


def _a_entero(valor):
    if valor is None:
        return None
    try:
        return int(valor)
    except (TypeError, ValueError):
        return None


class YouTubeAdapter(SocialProvider):
    platform_id = 'youtube'
    usa_pkce = False

    def build_authorize_url(self, state, redirect_uri, code_challenge=None):
        parametros = {
            'client_id': config.google_client_id(),
            'redirect_uri': redirect_uri,
            'response_type': 'code',
            'scope': ALCANCE_YOUTUBE,
            'access_type': 'offline',
            'prompt': 'consent',
            'state': state,
            'include_granted_scopes': 'true',
        }
        return 'https://accounts.google.com/o/oauth2/v2/auth?' + urllib.parse.urlencode(parametros)

    def exchange_code(self, code, redirect_uri, code_verifier=None):
        cuerpo = solicitar(
            'POST', 'https://oauth2.googleapis.com/token',
            data={
                'code': code,
                'client_id': config.google_client_id(),
                'client_secret': config.google_client_secret(),
                'redirect_uri': redirect_uri,
                'grant_type': 'authorization_code',
            },
            headers={'Content-Type': 'application/x-www-form-urlencoded'},
            clasificar_extra=_clasificar_google,
        )
        if 'access_token' not in cuerpo:
            raise SocialProviderError('desconocido', 'Google no devolvió un access_token', str(cuerpo))
        if not cuerpo.get('refresh_token'):
            raise SocialProviderError(
                'desconocido',
                'Google no devolvió un refresh_token. Si ya habías autorizado esta aplicación antes, '
                'revoca el acceso en myaccount.google.com/permissions y conecta de nuevo.',
            )
        canal = self._canal_propio(cuerpo['access_token'])
        return {
            'access_token': cuerpo['access_token'],
            'refresh_token': cuerpo.get('refresh_token'),
            'token_type': cuerpo.get('token_type', 'Bearer'),
            'expires_in': cuerpo.get('expires_in'),
            'refresh_expires_in': None,
            'scope': cuerpo.get('scope', ALCANCE_YOUTUBE),
            'external_user_id': (canal or {}).get('id'),
            'external_user_label': ((canal or {}).get('snippet') or {}).get('title'),
        }

    def refresh_token(self, refresh_token):
        cuerpo = solicitar(
            'POST', 'https://oauth2.googleapis.com/token',
            data={
                'refresh_token': refresh_token,
                'client_id': config.google_client_id(),
                'client_secret': config.google_client_secret(),
                'grant_type': 'refresh_token',
            },
            headers={'Content-Type': 'application/x-www-form-urlencoded'},
            clasificar_extra=_clasificar_google,
        )
        if 'access_token' not in cuerpo:
            raise SocialProviderError('refresh_expirado', 'Google rechazó el refresh token', str(cuerpo))
        return {
            'access_token': cuerpo['access_token'],
            'refresh_token': cuerpo.get('refresh_token'),
            'token_type': cuerpo.get('token_type', 'Bearer'),
            'expires_in': cuerpo.get('expires_in'),
            'refresh_expires_in': None,
            'scope': cuerpo.get('scope'),
        }

    def _canal_propio(self, access_token):
        try:
            cuerpo = solicitar(
                'GET', 'https://www.googleapis.com/youtube/v3/channels',
                params={'part': 'snippet,statistics', 'mine': 'true'},
                headers={'Authorization': f'Bearer {access_token}'},
                clasificar_extra=_clasificar_google,
            )
        except SocialProviderError:
            return None
        items = cuerpo.get('items') or []
        return items[0] if items else None

    def get_accounts(self, access_token):
        canal = self._canal_propio(access_token)
        if not canal:
            raise SocialProviderError('desconocido', 'No se pudo obtener el canal de YouTube')
        snippet = canal.get('snippet') or {}
        thumbs = snippet.get('thumbnails') or {}
        return [{
            'id_externo': canal['id'],
            'nombre': snippet.get('title', canal['id']),
            'usuario': None,
            'url_imagen': (thumbs.get('default') or {}).get('url'),
            'metadatos': {},
        }]

    def sync_profile(self, access_token, account):
        canal = self._canal_propio(access_token)
        if not canal:
            return {'seguidores': None, 'vistas_totales': None, 'publicaciones_totales': None}
        stats = canal.get('statistics') or {}
        oculto = stats.get('hiddenSubscriberCount')
        return {
            'seguidores': None if oculto else _a_entero(stats.get('subscriberCount')),
            'vistas_totales': _a_entero(stats.get('viewCount')),
            'publicaciones_totales': _a_entero(stats.get('videoCount')),
        }

    def sync_posts(self, access_token, account, limite=25):
        busqueda = solicitar(
            'GET', 'https://www.googleapis.com/youtube/v3/search',
            params={
                'part': 'id', 'forMine': 'true', 'type': 'video', 'order': 'date', 'maxResults': min(limite, 50),
            },
            headers={'Authorization': f'Bearer {access_token}'},
            clasificar_extra=_clasificar_google,
        )
        ids = [item['id']['videoId'] for item in busqueda.get('items', []) if item.get('id', {}).get('videoId')]
        if not ids:
            return []
        detalle = solicitar(
            'GET', 'https://www.googleapis.com/youtube/v3/videos',
            params={'part': 'snippet,statistics', 'id': ','.join(ids)},
            headers={'Authorization': f'Bearer {access_token}'},
            clasificar_extra=_clasificar_google,
        )
        resultados = []
        for v in detalle.get('items', []):
            snippet = v.get('snippet') or {}
            stats = v.get('statistics') or {}
            resultados.append({
                'id_externo_post': v['id'],
                'tipo': 'video',
                'permalink': f"https://www.youtube.com/watch?v={v['id']}",
                'extracto': (snippet.get('title') or '')[:500] or None,
                'publicado_at': snippet.get('publishedAt'),
                'metricas': {
                    'me_gusta': _a_entero(stats.get('likeCount')),
                    'comentarios': _a_entero(stats.get('commentCount')),
                    'compartidos': None,
                    'vistas': _a_entero(stats.get('viewCount')),
                    'impresiones': None,
                },
            })
        return resultados

    def revoke(self, access_token, refresh_token=None):
        token_a_revocar = refresh_token or access_token
        try:
            solicitar(
                'POST', 'https://oauth2.googleapis.com/revoke',
                data={'token': token_a_revocar},
                headers={'Content-Type': 'application/x-www-form-urlencoded'},
                clasificar_extra=_clasificar_google,
            )
            return True
        except SocialProviderError:
            return False

    def check_connection(self, access_token):
        return self._canal_propio(access_token) is not None
