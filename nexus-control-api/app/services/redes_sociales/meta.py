import os

from app.services.redes_sociales.comun import campo_requerido, metricas_resultado, solicitar_json

METRICA_IMPRESIONES_PAGINA = 'page_impressions'
METRICA_INTERACCIONES_PAGINA = 'page_post_engagements'
METRICA_ALCANCE_INSTAGRAM = 'reach'
METRICA_CUENTAS_ALCANZADAS_INSTAGRAM = 'accounts_engaged'


def _version_api():
    return os.environ.get('META_GRAPH_API_VERSION', 'v21.0').strip() or 'v21.0'


def _base_url():
    return f'https://graph.facebook.com/{_version_api()}'


def _ultimo_valor(datos_insights, nombre_metrica):
    for serie in datos_insights.get('data', []):
        if serie.get('name') != nombre_metrica:
            continue
        total = serie.get('total_value')
        if isinstance(total, dict):
            return total.get('value') or 0
        valores = serie.get('values') or []
        if not valores:
            return 0
        return valores[-1].get('value') or 0
    return 0


def obtener_metricas_facebook(credenciales):
    token = campo_requerido(credenciales, 'token_acceso')
    id_pagina = campo_requerido(credenciales, 'id_pagina')

    perfil = solicitar_json(
        'GET', f'{_base_url()}/{id_pagina}',
        params={'fields': 'fan_count', 'access_token': token},
    )
    insights = solicitar_json(
        'GET', f'{_base_url()}/{id_pagina}/insights',
        params={
            'metric': f'{METRICA_IMPRESIONES_PAGINA},{METRICA_INTERACCIONES_PAGINA}',
            'period': 'days_28',
            'access_token': token,
        },
    )

    impresiones = _ultimo_valor(insights, METRICA_IMPRESIONES_PAGINA)
    interacciones = _ultimo_valor(insights, METRICA_INTERACCIONES_PAGINA)

    return metricas_resultado(
        me_gusta=perfil.get('fan_count', 0),
        interacciones=interacciones,
        impresiones=impresiones,
    )


def obtener_metricas_instagram(credenciales):
    token = campo_requerido(credenciales, 'token_acceso')
    id_cuenta = campo_requerido(credenciales, 'id_cuenta_negocio')

    perfil = solicitar_json(
        'GET', f'{_base_url()}/{id_cuenta}',
        params={'fields': 'followers_count', 'access_token': token},
    )
    insights = solicitar_json(
        'GET', f'{_base_url()}/{id_cuenta}/insights',
        params={
            'metric': f'{METRICA_ALCANCE_INSTAGRAM},{METRICA_CUENTAS_ALCANZADAS_INSTAGRAM}',
            'period': 'days_28',
            'metric_type': 'total_value',
            'access_token': token,
        },
    )

    impresiones = _ultimo_valor(insights, METRICA_ALCANCE_INSTAGRAM)
    interacciones = _ultimo_valor(insights, METRICA_CUENTAS_ALCANZADAS_INSTAGRAM)

    return metricas_resultado(
        me_gusta=perfil.get('followers_count', 0),
        interacciones=interacciones,
        impresiones=impresiones,
    )
