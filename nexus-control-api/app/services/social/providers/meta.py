import urllib.parse

from app.services.social import config
from app.services.social.errors import SocialProviderError
from app.services.social.http_client import solicitar
from app.services.social.providers.base import SocialProvider

ALCANCE_FACEBOOK = 'pages_show_list,pages_read_engagement,pages_read_user_content,read_insights,business_management'
ALCANCE_INSTAGRAM = 'pages_show_list,pages_read_engagement,instagram_basic,instagram_manage_insights,business_management'


def _graph_base():
    return f'https://graph.facebook.com/{config.META_GRAPH_API_VERSION}'


def _clasificar_meta(status_code, cuerpo):
    if not isinstance(cuerpo, dict):
        return None
    error = cuerpo.get('error') or {}
    codigo = error.get('code')
    subcodigo = error.get('error_subcode')
    if codigo == 190:
        if subcodigo in (458, 460):
            return 'permisos_revocados'
        return 'token_expirado'
    if codigo in (4, 17, 32, 613):
        return 'limite_tasa'
    if codigo == 100 and 'does not exist' in str(error.get('message', '')).lower():
        return 'cuenta_eliminada'
    if codigo == 10:
        return 'permisos_revocados'
    return None


class MetaAdapter(SocialProvider):
    usa_pkce = False

    def __init__(self, modo):
        self.modo = modo
        self.platform_id = modo

    def _alcance(self):
        return ALCANCE_INSTAGRAM if self.modo == 'instagram' else ALCANCE_FACEBOOK

    def build_authorize_url(self, state, redirect_uri, code_challenge=None):
        parametros = {
            'client_id': config.meta_app_id(),
            'redirect_uri': redirect_uri,
            'state': state,
            'scope': self._alcance(),
            'response_type': 'code',
        }
        return f'https://www.facebook.com/{config.META_GRAPH_API_VERSION}/dialog/oauth?' + urllib.parse.urlencode(parametros)

    def exchange_code(self, code, redirect_uri, code_verifier=None):
        cuerpo = solicitar(
            'GET', f'{_graph_base()}/oauth/access_token',
            params={
                'client_id': config.meta_app_id(),
                'client_secret': config.meta_app_secret(),
                'redirect_uri': redirect_uri,
                'code': code,
            },
            clasificar_extra=_clasificar_meta,
        )
        corto = cuerpo.get('access_token')
        if not corto:
            raise SocialProviderError('desconocido', 'Meta no devolvió un access_token')

        largo = solicitar(
            'GET', f'{_graph_base()}/oauth/access_token',
            params={
                'grant_type': 'fb_exchange_token',
                'client_id': config.meta_app_id(),
                'client_secret': config.meta_app_secret(),
                'fb_exchange_token': corto,
            },
            clasificar_extra=_clasificar_meta,
        )

        token = largo.get('access_token', corto)
        expira_en = largo.get('expires_in') or cuerpo.get('expires_in')

        perfil = solicitar(
            'GET', f'{_graph_base()}/me',
            params={'fields': 'id,name', 'access_token': token},
            clasificar_extra=_clasificar_meta,
        )

        return {
            'access_token': token,
            'refresh_token': None,
            'token_type': largo.get('token_type', 'bearer'),
            'expires_in': expira_en,
            'refresh_expires_in': None,
            'scope': self._alcance(),
            'external_user_id': perfil.get('id'),
            'external_user_label': perfil.get('name'),
        }

    def refresh_token(self, refresh_token):
        raise SocialProviderError(
            'refresh_expirado',
            'Los tokens de usuario de Meta de larga duración no tienen refresh token; '
            'hay que volver a conectar esta plataforma antes de que expire (normalmente ~60 días).',
        )

    def get_accounts(self, access_token):
        cuerpo = solicitar(
            'GET', f'{_graph_base()}/me/accounts',
            params={'fields': 'id,name,access_token,picture{url}', 'access_token': access_token},
            clasificar_extra=_clasificar_meta,
        )
        paginas = cuerpo.get('data', [])
        if self.modo == 'facebook':
            return [
                {
                    'id_externo': p['id'],
                    'nombre': p.get('name', p['id']),
                    'usuario': None,
                    'url_imagen': ((p.get('picture') or {}).get('data') or {}).get('url'),
                    'metadatos': {},
                }
                for p in paginas
            ]

        cuentas = []
        for p in paginas:
            token_pagina = p.get('access_token')
            if not token_pagina:
                continue
            detalle = solicitar(
                'GET', f"{_graph_base()}/{p['id']}",
                params={'fields': 'instagram_business_account', 'access_token': token_pagina},
                clasificar_extra=_clasificar_meta,
            )
            ig = detalle.get('instagram_business_account')
            if not ig:
                continue
            perfil_ig = solicitar(
                'GET', f"{_graph_base()}/{ig['id']}",
                params={'fields': 'username,name,profile_picture_url', 'access_token': token_pagina},
                clasificar_extra=_clasificar_meta,
            )
            cuentas.append({
                'id_externo': ig['id'],
                'nombre': perfil_ig.get('name') or perfil_ig.get('username', ig['id']),
                'usuario': perfil_ig.get('username'),
                'url_imagen': perfil_ig.get('profile_picture_url'),
                'metadatos': {'pagina_id': p['id']},
            })
        return cuentas

    def _token_pagina(self, access_token, account):
        if self.modo == 'facebook':
            return access_token, account.id_externo

        pagina_id = (account.metadatos_json or {}).get('pagina_id')
        if not pagina_id:
            raise SocialProviderError(
                'cuenta_eliminada', 'No se encontró la página de Facebook vinculada a esta cuenta de Instagram',
            )
        cuerpo = solicitar(
            'GET', f'{_graph_base()}/me/accounts',
            params={'fields': 'id,access_token', 'access_token': access_token},
            clasificar_extra=_clasificar_meta,
        )
        for p in cuerpo.get('data', []):
            if p['id'] == pagina_id:
                return p.get('access_token'), account.id_externo
        raise SocialProviderError('cuenta_eliminada', 'La página de Facebook vinculada ya no está disponible')

    def sync_profile(self, access_token, account):
        token_pagina, id_objetivo = self._token_pagina(access_token, account)
        if self.modo == 'facebook':
            datos = solicitar(
                'GET', f'{_graph_base()}/{id_objetivo}',
                params={'fields': 'fan_count', 'access_token': token_pagina},
                clasificar_extra=_clasificar_meta,
            )
            return {'seguidores': datos.get('fan_count')}

        datos = solicitar(
            'GET', f'{_graph_base()}/{id_objetivo}',
            params={'fields': 'followers_count,media_count', 'access_token': token_pagina},
            clasificar_extra=_clasificar_meta,
        )
        return {
            'seguidores': datos.get('followers_count'),
            'publicaciones_totales': datos.get('media_count'),
        }

    def sync_posts(self, access_token, account, limite=25):
        token_pagina, id_objetivo = self._token_pagina(access_token, account)
        if self.modo == 'facebook':
            return self._sync_posts_facebook(token_pagina, id_objetivo, limite)
        return self._sync_posts_instagram(token_pagina, id_objetivo, limite)

    def _sync_posts_facebook(self, token_pagina, pagina_id, limite):
        cuerpo = solicitar(
            'GET', f'{_graph_base()}/{pagina_id}/posts',
            params={
                'fields': 'id,message,permalink_url,created_time,likes.summary(true),comments.summary(true),shares',
                'limit': limite,
                'access_token': token_pagina,
            },
            clasificar_extra=_clasificar_meta,
        )
        resultados = []
        for p in cuerpo.get('data', []):
            insights = self._insights_post_facebook(token_pagina, p['id'])
            resultados.append({
                'id_externo_post': p['id'],
                'tipo': 'post',
                'permalink': p.get('permalink_url'),
                'extracto': (p.get('message') or '')[:500] or None,
                'publicado_at': p.get('created_time'),
                'metricas': {
                    'me_gusta': ((p.get('likes') or {}).get('summary') or {}).get('total_count'),
                    'comentarios': ((p.get('comments') or {}).get('summary') or {}).get('total_count'),
                    'compartidos': (p.get('shares') or {}).get('count'),
                    'impresiones': insights.get('post_impressions'),
                    'vistas': None,
                },
            })
        return resultados

    def _insights_post_facebook(self, token_pagina, post_id):
        try:
            cuerpo = solicitar(
                'GET', f'{_graph_base()}/{post_id}/insights',
                params={'metric': 'post_impressions', 'access_token': token_pagina},
                clasificar_extra=_clasificar_meta,
            )
        except SocialProviderError:
            return {}
        valores = {}
        for item in cuerpo.get('data', []):
            serie = item.get('values') or []
            if serie:
                valores[item.get('name')] = serie[-1].get('value')
        return valores

    def _sync_posts_instagram(self, token_pagina, ig_id, limite):
        cuerpo = solicitar(
            'GET', f'{_graph_base()}/{ig_id}/media',
            params={
                'fields': 'id,caption,media_type,permalink,timestamp,like_count,comments_count',
                'limit': limite,
                'access_token': token_pagina,
            },
            clasificar_extra=_clasificar_meta,
        )
        resultados = []
        for m in cuerpo.get('data', []):
            insights = self._insights_media_instagram(token_pagina, m['id'], m.get('media_type'))
            resultados.append({
                'id_externo_post': m['id'],
                'tipo': (m.get('media_type') or 'post').lower(),
                'permalink': m.get('permalink'),
                'extracto': (m.get('caption') or '')[:500] or None,
                'publicado_at': m.get('timestamp'),
                'metricas': {
                    'me_gusta': m.get('like_count'),
                    'comentarios': m.get('comments_count'),
                    'compartidos': None,
                    'impresiones': insights.get('impressions'),
                    'vistas': insights.get('reach'),
                },
            })
        return resultados

    def _insights_media_instagram(self, token_pagina, media_id, media_type):
        metricas = 'impressions,reach,engagement' if media_type != 'STORY' else 'impressions,reach'
        try:
            cuerpo = solicitar(
                'GET', f'{_graph_base()}/{media_id}/insights',
                params={'metric': metricas, 'access_token': token_pagina},
                clasificar_extra=_clasificar_meta,
            )
        except SocialProviderError:
            return {}
        valores = {}
        for item in cuerpo.get('data', []):
            serie = item.get('values') or []
            if serie:
                valores[item.get('name')] = serie[-1].get('value')
        return valores

    def revoke(self, access_token, refresh_token=None):
        try:
            solicitar(
                'DELETE', f'{_graph_base()}/me/permissions',
                params={'access_token': access_token},
                clasificar_extra=_clasificar_meta,
            )
            return True
        except SocialProviderError:
            return False

    def check_connection(self, access_token):
        try:
            solicitar(
                'GET', f'{_graph_base()}/me',
                params={'fields': 'id', 'access_token': access_token},
                clasificar_extra=_clasificar_meta,
            )
            return True
        except SocialProviderError:
            return False
