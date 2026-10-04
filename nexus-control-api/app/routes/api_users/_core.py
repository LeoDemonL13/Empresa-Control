from flask import Blueprint

from app.constants import ROLE_ADMIN, ROLE_SUPER_ADMIN
from app.models import User

bp = Blueprint('api_users', __name__, url_prefix='/api/users')

_ROLE_ORDER = {ROLE_SUPER_ADMIN: 0, ROLE_ADMIN: 1}


def _user_to_dict(u: User) -> dict:
    return {
        'id': u.id,
        'username': u.username,
        'role': u.role,
        'full_name': u.full_name,
        'position': u.position,
        'contact_info': u.contact_info,
        'permisos': u.permisos,
        'totp_enabled': bool(u.totp_secret),
        'activo': bool(u.activo),
        'last_seen': u.last_seen.isoformat() if u.last_seen else None,
        'created_at': u.created_at.isoformat() if u.created_at else None,
    }
