import urllib.parse

from app.services.social import config
from app.services.social.errors import SocialProviderError
from app.services.social.http_client import solicitar
from app.services.social.providers.base import SocialProvider

ALCANCE_TIKTOK = 'user.info.basic,user.info.stats,video.list'
CAMPOS_USUARIO = 'open_id,display_name,avatar_url,follower_count,likes_count,video_count'
CAMPOS_VIDEO = (
    'id,title,video_description,create_time,cover_image_url,share_url,'
    'view_count,like_count,comment_count,share_count'
)


def _clasificar_tiktok(status_code, cuerpo):
    if not isinstance(cuerpo, dict):
        return None
    error = cuerpo.get('error')
    codigo = error.get('code') if isinstance(error, dict) else error
    if codigo in ('access_token_invalid', 'access_token_expired'):
        return 'token_expirado'
    if codigo in ('refresh_token_invalid', 'refresh_token_expired'):
        return 'refresh_expirado'
    if codigo == 'scope_not_authorized':
        return 'permisos_revocados'
    if codigo == 'rate_limit_exceeded':
        return 'limite_tasa'
    return None


class TikTokAdapter(SocialProvider):
    platform_id = 'tiktok'
    usa_pkce = True

    def build_authorize_url(self, state, redirect_uri, code_challenge=None):
        parametros = {
            'client_key': config.tiktok_client_key(),
            'scope': ALCANCE_TIKTOK,
            'response_type': 'code',
            'redirect_uri': redirect_uri,
            'state': state,
        }
        if code_challenge:
            parametros['code_challenge'] = code_challenge
            parametros['code_challenge_method'] = 'S256'
        return 'https://www.tiktok.com/v2/auth/authorize?' + urllib.parse.urlencode(parametros)

    def exchange_code(self, code, redirect_uri, code_verifier=None):
        datos = {
            'client_key': config.tiktok_client_key(),
            'client_secret': config.tiktok_client_secret(),
            'code': code,
            'grant_type': 'authorization_code',
            'redirect_uri': redirect_uri,
        }
        if code_verifier:
            datos['code_verifier'] = code_verifier
        cuerpo = solicitar(
            'POST', 'https://open.tiktokapis.com/v2/oauth/token/',
            data=datos,
            headers={'Content-Type': 'application/x-www-form-urlencoded'},
            clasificar_extra=_clasificar_tiktok,
        )
        if 'access_token' not in cuerpo:
            raise SocialProviderError('desconocido', 'TikTok no devolvió un access_token', str(cuerpo))
        perfil = self._info_usuario(cuerpo['access_token']) or {}
        return {
            'access_token': cuerpo['access_token'],
            'refresh_token': cuerpo.get('refresh_token'),
            'token_type': cuerpo.get('token_type', 'Bearer'),
            'expires_in': cuerpo.get('expires_in'),
            'refresh_expires_in': cuerpo.get('refresh_expires_in'),
            'scope': cuerpo.get('scope', ALCANCE_TIKTOK),
            'external_user_id': cuerpo.get('open_id'),
            'external_user_label': perfil.get('display_name'),
        }

    def refresh_token(self, refresh_token):
        cuerpo = solicitar(
            'POST', 'https://open.tiktokapis.com/v2/oauth/token/',
            data={
                'client_key': config.tiktok_client_key(),
                'client_secret': config.tiktok_client_secret(),
                'grant_type': 'refresh_token',
                'refresh_token': refresh_token,
            },
            headers={'Content-Type': 'application/x-www-form-urlencoded'},
            clasificar_extra=_clasificar_tiktok,
        )
        if 'access_token' not in cuerpo:
            raise SocialProviderError('refresh_expirado', 'TikTok rechazó el refresh token', str(cuerpo))
        return {
            'access_token': cuerpo['access_token'],
            'refresh_token': cuerpo.get('refresh_token'),
            'token_type': cuerpo.get('token_type', 'Bearer'),
            'expires_in': cuerpo.get('expires_in'),
            'refresh_expires_in': cuerpo.get('refresh_expires_in'),
            'scope': cuerpo.get('scope'),
        }

    def _info_usuario(self, access_token, campos=CAMPOS_USUARIO):
        try:
            cuerpo = solicitar(
                'GET', 'https://open.tiktokapis.com/v2/user/info/',
                params={'fields': campos},
                headers={'Authorization': f'Bearer {access_token}'},
                clasificar_extra=_clasificar_tiktok,
            )
        except SocialProviderError:
            return None
        return (cuerpo.get('data') or {}).get('user')

    def get_accounts(self, access_token):
        perfil = self._info_usuario(access_token)
        if not perfil:
            raise SocialProviderError('desconocido', 'No se pudo obtener el perfil de TikTok')
        return [{
            'id_externo': perfil.get('open_id'),
            'nombre': perfil.get('display_name', 'Cuenta de TikTok'),
            'usuario': None,
            'url_imagen': perfil.get('avatar_url'),
            'metadatos': {},
        }]

    def sync_profile(self, access_token, account):
        perfil = self._info_usuario(access_token)
        if not perfil:
            return {'seguidores': None, 'me_gusta_totales': None, 'publicaciones_totales': None}
        return {
            'seguidores': perfil.get('follower_count'),
            'me_gusta_totales': perfil.get('likes_count'),
            'publicaciones_totales': perfil.get('video_count'),
        }

    def sync_posts(self, access_token, account, limite=25):
        cuerpo = solicitar(
            'POST', 'https://open.tiktokapis.com/v2/video/list/',
            params={'fields': CAMPOS_VIDEO},
            json={'max_count': min(limite, 20)},
            headers={'Authorization': f'Bearer {access_token}', 'Content-Type': 'application/json'},
            clasificar_extra=_clasificar_tiktok,
        )
        videos = (cuerpo.get('data') or {}).get('videos', [])
        resultados = []
        for v in videos:
            resultados.append({
                'id_externo_post': v['id'],
                'tipo': 'video',
                'permalink': v.get('share_url'),
                'extracto': (v.get('video_description') or v.get('title') or '')[:500] or None,
                'publicado_at': v.get('create_time'),
                'metricas': {
                    'me_gusta': v.get('like_count'),
                    'comentarios': v.get('comment_count'),
                    'compartidos': v.get('share_count'),
                    'vistas': v.get('view_count'),
                    'impresiones': None,
                },
            })
        return resultados

    def revoke(self, access_token, refresh_token=None):
        try:
            solicitar(
                'POST', 'https://open.tiktokapis.com/v2/oauth/revoke/',
                data={
                    'client_key': config.tiktok_client_key(),
                    'client_secret': config.tiktok_client_secret(),
                    'token': refresh_token or access_token,
                },
                headers={'Content-Type': 'application/x-www-form-urlencoded'},
                clasificar_extra=_clasificar_tiktok,
            )
            return True
        except SocialProviderError:
            return False

    def check_connection(self, access_token):
        return self._info_usuario(access_token, campos='open_id') is not None
