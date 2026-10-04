from app.services.social.providers.base import SocialProvider
from app.services.social.providers.meta import MetaAdapter
from app.services.social.providers.tiktok import TikTokAdapter
from app.services.social.providers.youtube import YouTubeAdapter

_REGISTRO = {
    'facebook': MetaAdapter('facebook'),
    'instagram': MetaAdapter('instagram'),
    'tiktok': TikTokAdapter(),
    'youtube': YouTubeAdapter(),
}


def proveedor_para(plataforma: str) -> SocialProvider:
    proveedor = _REGISTRO.get(plataforma)
    if not proveedor:
        raise ValueError(f'Plataforma no soportada: {plataforma}')
    return proveedor


def plataformas_disponibles():
    return tuple(_REGISTRO.keys())
