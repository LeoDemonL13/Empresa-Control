import hashlib

from flask import Blueprint, current_app, request
from werkzeug.security import generate_password_hash

from app.models import User

bp = Blueprint('api_auth', __name__, url_prefix='/api/auth')


@bp.after_request
def _no_store_on_auth_responses(response):
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response


ACCESS_TOKEN_LIFETIME_MINUTES = 20
PRE_2FA_LIFETIME_SECONDS = 300
_RT_COOKIE = 'rt_api'
_RT_COOKIE_PATH = '/api/auth'

_MAX_USERNAME_LEN = 80
_MAX_PASSWORD_LEN = 256
_MAX_TOTP_CODE_LEN = 8
_MAX_BACKUP_CODE_LEN = 32
_BACKUP_CODES_COUNT = 10
_BACKUP_CODES_LOW_THRESHOLD = 3

_JWT_ISS = 'nexus-control-api'
_JWT_AUD = 'nexus-control-panel'

_SETUP_2FA_TTL = 600
_MAX_ACTIVE_RT_PER_USER = 8
_RT_ROTATION_GRACE_SECONDS = 10

_LOGIN_FAILS_WINDOW = 15 * 60
_LOGIN_FAILS_THRESHOLD = 5
_LOCKOUT_LEVEL_TTL = 24 * 3600
_LOCKOUT_DURATIONS = [
    10 * 60,
    30 * 60,
    60 * 60,
    3 * 60 * 60,
    12 * 60 * 60,
    24 * 60 * 60,
]


def _jwt_secret() -> str:
    return current_app.config.get('JWT_SECRET_KEY') or current_app.config['SECRET_KEY']


def _user_to_dict(user: User) -> dict:
    return {
        'id': user.id,
        'username': user.username,
        'role': user.role,
        'full_name': user.full_name,
        'position': user.position,
        'contact_info': user.contact_info,
        'profile_pic': user.profile_pic,
        'totp_enabled': bool(user.totp_secret),
        'activo': bool(user.activo),
        'permisos': user.permisos,
        'last_seen': user.last_seen.isoformat() if user.last_seen else None,
        'created_at': user.created_at.isoformat() if user.created_at else None,
    }


def _is_admin_user(user: User) -> bool:
    return user.role in ('admin', 'super_admin')


def _cookie_samesite() -> str:
    import os
    return os.environ.get('RT_COOKIE_SAMESITE', 'Lax')


def _cookie_secure() -> bool:
    if _cookie_samesite().lower() == 'none':
        return True
    return request.is_secure


def _csrf_protected_cookie_endpoint():
    from flask import jsonify
    xrw = request.headers.get('X-Requested-With', '').strip().lower()
    if xrw != 'xmlhttprequest':
        return jsonify({'error': 'Header X-Requested-With requerido'}), 403
    return None


_DUMMY_PW_HASH = generate_password_hash('not-a-real-password-timing-dummy')


def _norm_user(username: str) -> str:
    return (username or '').lower().strip()


def _lockout_key(username):
    return f"login_lockout:{_norm_user(username)}"


def _level_key(username):
    return f"login_lockout_level:{_norm_user(username)}"


def _fails_key(username):
    return f"login_fails:{_norm_user(username)}"


def _check_lockout(username):
    from app.extensions import redis_call
    if not _norm_user(username):
        return None
    ttl = redis_call(lambda r: r.ttl(_lockout_key(username)))
    return ttl if (ttl is not None and ttl > 0) else None


def _register_login_failure(username):
    from app.extensions import redis_call
    if not _norm_user(username):
        return

    def _registrar(r):
        fkey = _fails_key(username)
        fails = r.incr(fkey)
        if fails == 1:
            r.expire(fkey, _LOGIN_FAILS_WINDOW)
        if fails >= _LOGIN_FAILS_THRESHOLD:
            lkey = _level_key(username)
            try:
                level = int(r.get(lkey) or 0)
            except (TypeError, ValueError):
                level = 0
            duration = _LOCKOUT_DURATIONS[min(level, len(_LOCKOUT_DURATIONS) - 1)]
            r.setex(_lockout_key(username), duration, '1')
            r.setex(lkey, _LOCKOUT_LEVEL_TTL, level + 1)
            r.delete(fkey)

    redis_call(_registrar)


def _clear_login_failures(username):
    from app.extensions import redis_call
    if not _norm_user(username):
        return
    redis_call(lambda r: r.delete(
        _fails_key(username), _lockout_key(username), _level_key(username),
    ))


def _format_ttl(seconds: int) -> str:
    if seconds <= 60:
        return "1 minuto"
    if seconds < 3600:
        m = (seconds + 59) // 60
        return f"{m} minutos"
    if seconds < 86400:
        h = (seconds + 3599) // 3600
        return f"{h} {'hora' if h == 1 else 'horas'}"
    d = (seconds + 86399) // 86400
    return f"{d} {'día' if d == 1 else 'días'}"


def _hash_token(raw: str) -> str:
    return hashlib.sha256(raw.encode()).hexdigest()
