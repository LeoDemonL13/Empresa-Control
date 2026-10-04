from flask import Blueprint

from app.models import ConexionRedSocial

bp = Blueprint('api_conexiones_sociales', __name__, url_prefix='/api/conexiones-sociales')


def _conexion_to_dict(c: ConexionRedSocial) -> dict:
    return {
        'plataforma': c.plataforma,
        'conectada': bool(c.credenciales_cifradas),
        'ultima_sincronizacion': c.ultima_sincronizacion.isoformat() if c.ultima_sincronizacion else None,
        'ultimo_error': c.ultimo_error,
        'actualizado_por': c.actualizado_por,
        'updated_at': c.updated_at.isoformat() if c.updated_at else None,
    }


def _conexion_vacia(plataforma: str) -> dict:
    return {
        'plataforma': plataforma,
        'conectada': False,
        'ultima_sincronizacion': None,
        'ultimo_error': None,
        'actualizado_por': None,
        'updated_at': None,
    }
