from flask import Blueprint

from app.models import AuditLog

bp = Blueprint('api_bitacora', __name__, url_prefix='/api/bitacora')


def _log_to_dict(log: AuditLog) -> dict:
    return {
        'id': log.id,
        'user': log.user or 'Sistema',
        'action': log.action,
        'entidad': log.entidad,
        'entidad_id': log.entidad_id,
        'origen': log.origen,
        'ip': log.ip,
        'created_at': log.created_at.isoformat() if log.created_at else None,
    }


def _log_to_dict_detalle(log: AuditLog) -> dict:
    d = _log_to_dict(log)
    d['detalle'] = log.detalle
    return d
