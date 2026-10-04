from datetime import datetime, timezone

from flask import Blueprint

from app.constants import OFFLINE_AFTER_SECONDS
from app.models import Equipo

bp = Blueprint('api_equipos', __name__, url_prefix='/api/equipos')


def _esta_en_linea(equipo: Equipo) -> bool:
    if not equipo.ultimo_latido:
        return False
    ultimo = equipo.ultimo_latido
    if ultimo.tzinfo is None:
        ultimo = ultimo.replace(tzinfo=timezone.utc)
    return (datetime.now(timezone.utc) - ultimo).total_seconds() <= OFFLINE_AFTER_SECONDS


def _equipo_to_dict(equipo: Equipo) -> dict:
    return {
        'id': equipo.id,
        'nombre': equipo.nombre,
        'hostname': equipo.hostname,
        'ip': equipo.ip,
        'mac': equipo.mac,
        'usuario_asignado': equipo.usuario_asignado,
        'sistema_operativo': equipo.sistema_operativo,
        'agente_version': equipo.agente_version,
        'categoria': {'id': equipo.categoria.id, 'nombre': equipo.categoria.nombre} if equipo.categoria else None,
        'en_linea': _esta_en_linea(equipo),
        'enrolado': bool(equipo.api_key_hash),
        'ultimo_latido': equipo.ultimo_latido.isoformat() if equipo.ultimo_latido else None,
        'activo': bool(equipo.activo),
        'created_at': equipo.created_at.isoformat() if equipo.created_at else None,
    }
