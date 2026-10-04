import json as _json
import secrets
from datetime import datetime, timedelta, timezone

import jwt
from flask import request

from app.constants import REFRESH_TOKEN_LIFETIME_DAYS
from app.extensions import db
from app.models import RefreshToken, User

from ._core import (
    ACCESS_TOKEN_LIFETIME_MINUTES,
    PRE_2FA_LIFETIME_SECONDS,
    _JWT_AUD,
    _JWT_ISS,
    _MAX_ACTIVE_RT_PER_USER,
    _RT_COOKIE,
    _RT_COOKIE_PATH,
    _RT_ROTATION_GRACE_SECONDS,
    _cookie_samesite,
    _cookie_secure,
    _hash_token,
    _jwt_secret,
)


def _encode_access_token(user: User) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        'sub': str(user.id),
        'username': user.username,
        'role': user.role,
        'pv': user.password_version or 1,
        'iat': int(now.timestamp()),
        'exp': int((now + timedelta(minutes=ACCESS_TOKEN_LIFETIME_MINUTES)).timestamp()),
        'jti': secrets.token_urlsafe(16),
        'type': 'access',
        'iss': _JWT_ISS,
        'aud': _JWT_AUD,
    }
    return jwt.encode(payload, _jwt_secret(), algorithm='HS256')


def _encode_pre_2fa_token(user: User) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        'sub': str(user.id),
        'pv': user.password_version or 1,
        'iat': int(now.timestamp()),
        'exp': int((now + timedelta(seconds=PRE_2FA_LIFETIME_SECONDS)).timestamp()),
        'jti': secrets.token_urlsafe(16),
        'type': 'pre_2fa',
        'iss': _JWT_ISS,
        'aud': _JWT_AUD,
    }
    return jwt.encode(payload, _jwt_secret(), algorithm='HS256')


def _decode_token(token: str, expected_type: str) -> dict | None:
    try:
        payload = jwt.decode(
            token,
            _jwt_secret(),
            algorithms=['HS256'],
            audience=_JWT_AUD,
            issuer=_JWT_ISS,
            options={'require': ['exp', 'iat', 'sub', 'type']},
        )
    except jwt.PyJWTError:
        return None
    if payload.get('type') != expected_type:
        return None
    return payload


def _revoke_jti(jti: str, exp_ts: int) -> None:
    from app.extensions import redis_call
    ttl = max(1, int(exp_ts - datetime.now(timezone.utc).timestamp()))
    redis_call(lambda r: r.setex(f'jwt_revoked:{jti}', ttl, '1'))


def _is_jti_revoked(jti: str) -> bool:
    from app.extensions import redis_call
    return bool(redis_call(lambda r: r.get(f'jwt_revoked:{jti}'), default=False))


def _burn_pre_2fa_jti(jti: str, exp_ts: int) -> bool:
    if not jti:
        return True
    from app.extensions import redis_call
    ttl = max(1, int(exp_ts - datetime.now(timezone.utc).timestamp()))
    return bool(redis_call(
        lambda r: r.set(f'pre2fa_used:{jti}', '1', nx=True, ex=ttl),
        default=True,
    ))


def _totp_code_already_used(user_id: int, code: str) -> bool:
    from app.extensions import redis_call
    import hashlib
    h = hashlib.sha256(f'{user_id}:{code}'.encode()).hexdigest()
    key = f'totp_used:{h}'
    was_set = redis_call(lambda r: r.set(key, '1', nx=True, ex=90), default=True)
    return not was_set


def _store_rt_meta(rt_id: int) -> None:
    from app.extensions import get_real_client_ip_flask, redis_call
    ua = (request.headers.get('User-Agent') or '')[:200] if request else ''
    ip = get_real_client_ip_flask() if request else ''
    payload = _json.dumps({'ua': ua, 'ip': ip})
    ttl = REFRESH_TOKEN_LIFETIME_DAYS * 86400 + 86400
    redis_call(lambda r: r.setex(f'rt_meta:{rt_id}', ttl, payload))


def _load_rt_meta(rt_id: int) -> dict:
    from app.extensions import redis_call
    raw = redis_call(lambda r: r.get(f'rt_meta:{rt_id}'))
    if not raw:
        return {}
    try:
        return _json.loads(raw)
    except Exception:
        return {}


def _mark_rt_just_rotated(rt_id: int) -> None:
    from app.extensions import redis_call
    redis_call(lambda r: r.setex(f'rt_just_rotated:{rt_id}', _RT_ROTATION_GRACE_SECONDS, '1'))


def _is_rt_just_rotated(rt_id: int) -> bool:
    from app.extensions import redis_call
    return bool(redis_call(lambda r: r.get(f'rt_just_rotated:{rt_id}'), default=False))


def _enforce_rt_cap(user_id: int) -> None:
    activos = (
        RefreshToken.query
        .filter_by(user_id=user_id, revoked=False)
        .order_by(RefreshToken.created_at.asc())
        .all()
    )
    sobrante = len(activos) - (_MAX_ACTIVE_RT_PER_USER - 1)
    if sobrante <= 0:
        return
    ids_a_revocar = [t.id for t in activos[:sobrante]]
    (
        db.session.query(RefreshToken)
        .filter(RefreshToken.id.in_(ids_a_revocar))
        .update({RefreshToken.revoked: True}, synchronize_session=False)
    )


def _issue_refresh_token(user_id: int) -> str:
    _enforce_rt_cap(user_id)
    raw = secrets.token_urlsafe(32)
    expires = datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_LIFETIME_DAYS)
    tok = RefreshToken(token_hash=_hash_token(raw), user_id=user_id, expires_at=expires)
    db.session.add(tok)
    db.session.commit()
    _store_rt_meta(tok.id)
    return raw


def _set_rt_cookie(response, raw: str) -> None:
    _delete_legacy_root_cookie(response)
    response.set_cookie(
        _RT_COOKIE,
        raw,
        max_age=REFRESH_TOKEN_LIFETIME_DAYS * 86400,
        httponly=True,
        secure=_cookie_secure(),
        samesite=_cookie_samesite(),
        path=_RT_COOKIE_PATH,
    )


def _delete_legacy_root_cookie(response) -> None:
    response.delete_cookie(
        _RT_COOKIE, path='/', secure=_cookie_secure(), samesite=_cookie_samesite(),
    )


def _clear_rt_cookie(response) -> None:
    response.delete_cookie(
        _RT_COOKIE, path=_RT_COOKIE_PATH, secure=_cookie_secure(), samesite=_cookie_samesite(),
    )
    _delete_legacy_root_cookie(response)
