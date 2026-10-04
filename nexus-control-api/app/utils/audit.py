import logging

from flask import g

from app.extensions import db, get_real_client_ip_flask
from app.models import AuditLog
from app.utils.security import _safe_log_value

logger = logging.getLogger(__name__)


def log_action(action, entidad=None, entidad_id=None, detalle=None, origen='panel'):
    try:
        ip = get_real_client_ip_flask()
        jwt_user = getattr(g, '_jwt_user', None)
        username = jwt_user.username if jwt_user is not None else 'anon'
        db.session.add(AuditLog(
            user=_safe_log_value(username, 80),
            user_id=jwt_user.id if jwt_user is not None else None,
            action=_safe_log_value(action, 200),
            entidad=_safe_log_value(entidad, 60) if entidad else None,
            entidad_id=entidad_id,
            detalle=detalle,
            origen=origen,
            ip=ip,
        ))
        db.session.commit()
    except Exception as e:
        try:
            db.session.rollback()
        except Exception:
            pass
        logger.warning(
            "Error guardando log de auditoría (acción: %s): %s",
            _safe_log_value(action, 100), e,
        )
