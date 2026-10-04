from flask import Blueprint

from app.models import MetricaSocial

bp = Blueprint('api_metricas', __name__, url_prefix='/api/metricas-sociales')


def _metrica_to_dict(m: MetricaSocial) -> dict:
    return {
        'id': m.id,
        'red_social': m.red_social,
        'me_gusta': m.me_gusta,
        'interacciones': m.interacciones,
        'impresiones': m.impresiones,
        'engagement': m.engagement,
        'origen': m.origen,
        'actualizado_por': m.actualizado_por,
        'updated_at': m.updated_at.isoformat() if m.updated_at else None,
    }
