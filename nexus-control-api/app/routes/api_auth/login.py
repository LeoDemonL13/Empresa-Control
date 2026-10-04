import secrets
from datetime import datetime, timedelta, timezone

import pyotp
from flask import g, jsonify, request
from werkzeug.security import check_password_hash

from app.constants import REFRESH_TOKEN_LIFETIME_DAYS
from app.extensions import db, limiter
from app.models import RefreshToken, User
from app.utils import log_action

from ._core import (
    _DUMMY_PW_HASH,
    _MAX_BACKUP_CODE_LEN,
    _MAX_PASSWORD_LEN,
    _MAX_TOTP_CODE_LEN,
    _MAX_USERNAME_LEN,
    _RT_COOKIE,
    _check_lockout,
    _clear_login_failures,
    _csrf_protected_cookie_endpoint,
    _format_ttl,
    _hash_token,
    _register_login_failure,
    _user_to_dict,
    bp,
)
from .tokens import (
    _burn_pre_2fa_jti,
    _clear_rt_cookie,
    _decode_token,
    _encode_access_token,
    _encode_pre_2fa_token,
    _is_rt_just_rotated,
    _issue_refresh_token,
    _mark_rt_just_rotated,
    _revoke_jti,
    _set_rt_cookie,
    _store_rt_meta,
    _totp_code_already_used,
)
from .twofa import (
    _BACKUP_CODES_COUNT,
    _check_twofa_lockout,
    _clear_twofa_failures,
    _count_active_backup_codes,
    _register_twofa_failure,
    _try_consume_backup_code,
)


@bp.route('/login', methods=['POST'])
@limiter.limit("4 per minute")
@limiter.limit(
    "8 per minute",
    key_func=lambda: f"api_login_user:{((request.get_json(silent=True) or {}).get('username') or '').lower().strip()}",
)
def api_login():
    data = request.get_json(silent=True) or {}
    username = (data.get('username') or '').strip()
    password = data.get('password') or ''

    if not username or not password:
        return jsonify({'error': 'Usuario y contraseña son obligatorios'}), 400
    if len(username) > _MAX_USERNAME_LEN or len(password) > _MAX_PASSWORD_LEN:
        return jsonify({'error': 'Credenciales incorrectas'}), 401

    lockout_ttl = _check_lockout(username)
    if lockout_ttl:
        return jsonify({
            'error': f'Cuenta bloqueada por demasiados intentos. Intenta en {_format_ttl(lockout_ttl)}.',
        }), 423

    u = User.query.filter_by(username=username).first()
    if u:
        password_ok = check_password_hash(u.password_hash, password)
    else:
        check_password_hash(_DUMMY_PW_HASH, password)
        password_ok = False

    if not password_ok:
        _register_login_failure(username)
        post_fail_ttl = _check_lockout(username)
        if post_fail_ttl:
            return jsonify({
                'error': f'Cuenta bloqueada por demasiados intentos. Intenta en {_format_ttl(post_fail_ttl)}.',
            }), 423
        from app.extensions import get_real_client_ip_flask
        if u:
            g._jwt_user = u
        log_action(f"Login fallido para '{username[:80]}' desde IP {get_real_client_ip_flask()}")
        return jsonify({'error': 'Credenciales incorrectas'}), 401

    _clear_login_failures(username)

    if not u.activo:
        from app.extensions import get_real_client_ip_flask
        log_action(f"Login rechazado: cuenta desactivada '{username[:80]}' desde IP {get_real_client_ip_flask()}")
        return jsonify({'error': 'Tu cuenta está desactivada. Contacta al súper administrador.'}), 403

    if u.totp_secret:
        return jsonify({
            'requires2fa': True,
            'stepToken': _encode_pre_2fa_token(u),
        })

    token = _encode_access_token(u)
    u.last_seen = datetime.now()
    db.session.commit()
    g._jwt_user = u
    from app.extensions import get_real_client_ip_flask
    log_action(f"Login exitoso desde IP {get_real_client_ip_flask()}")

    resp = jsonify({'token': token, 'user': _user_to_dict(u)})
    _set_rt_cookie(resp, _issue_refresh_token(u.id))
    return resp


def _api_verify_2fa_user_key() -> str:
    data = request.get_json(silent=True) or {}
    step = data.get('stepToken') or ''
    if not step or not isinstance(step, str):
        return 'api_v2fa_user:anon'
    return f'api_v2fa_user:{_hash_token(step)[:16]}'


@bp.route('/verify-2fa', methods=['POST'])
@limiter.limit("4 per minute")
@limiter.limit("8 per minute", key_func=_api_verify_2fa_user_key)
def api_verify_2fa():
    data = request.get_json(silent=True) or {}
    step_token = data.get('stepToken') or ''
    code = (data.get('code') or '').strip()
    if len(code) > _MAX_BACKUP_CODE_LEN:
        return jsonify({'error': 'Código inválido'}), 401

    payload = _decode_token(step_token, 'pre_2fa')
    if not payload:
        return jsonify({'error': 'Sesión 2FA expirada. Inicia sesión de nuevo.'}), 401

    try:
        uid = int(payload['sub'])
    except (TypeError, ValueError, KeyError):
        return jsonify({'error': 'Sesión inválida. Inicia sesión de nuevo.'}), 401

    lock_ttl = _check_twofa_lockout(uid)
    if lock_ttl:
        return jsonify({
            'error': f'Demasiados intentos 2FA fallidos. Intenta de nuevo en {_format_ttl(lock_ttl)}.',
        }), 423

    user = db.session.get(User, uid)
    if not user or not user.totp_secret:
        return jsonify({'error': 'Sesión inválida. Inicia sesión de nuevo.'}), 401
    if (user.password_version or 1) != payload.get('pv', 1):
        return jsonify({'error': 'Tu contraseña cambió. Inicia sesión de nuevo.'}), 401

    g._jwt_user = user

    totp_ok = len(code) <= _MAX_TOTP_CODE_LEN and pyotp.TOTP(user.totp_secret).verify(code, valid_window=1)
    backup_used = False
    if not totp_ok:
        backup_used = _try_consume_backup_code(uid, code)

    if not totp_ok and not backup_used:
        _register_twofa_failure(uid)
        post_fail_ttl = _check_twofa_lockout(uid)
        if post_fail_ttl:
            return jsonify({
                'error': f'Cuenta bloqueada por 2FA fallido. Intenta en {_format_ttl(post_fail_ttl)}.',
            }), 423
        log_action(f"2FA fallido para {user.username}")
        return jsonify({'error': 'Código incorrecto'}), 401

    if totp_ok and _totp_code_already_used(user.id, code):
        log_action(f"2FA repetido bloqueado para {user.username}")
        return jsonify({'error': 'Este código ya fue usado. Espera al siguiente.'}), 401

    if not _burn_pre_2fa_jti(payload.get('jti'), int(payload['exp'])):
        log_action(f"stepToken de 2FA reusado y bloqueado para {user.username}")
        return jsonify({'error': 'Esta sesión de 2FA ya fue usada. Inicia sesión de nuevo.'}), 401

    _clear_twofa_failures(user.id)

    if backup_used:
        remaining = _count_active_backup_codes(user.id)
        log_action(f"Login 2FA con código de respaldo para {user.username} (restantes: {remaining})")

    token = _encode_access_token(user)
    user.last_seen = datetime.now()
    db.session.commit()
    log_action(f"Login 2FA exitoso para {user.username}")

    resp = jsonify({'token': token, 'user': _user_to_dict(user)})
    _set_rt_cookie(resp, _issue_refresh_token(user.id))
    return resp


def _api_refresh_user_key() -> str:
    raw_rt = request.cookies.get(_RT_COOKIE)
    if not raw_rt:
        return 'api_refresh:no_cookie'
    return f'api_refresh:{_hash_token(raw_rt)[:16]}'


@bp.route('/refresh', methods=['POST'])
@limiter.limit("30 per minute")
@limiter.limit("15 per minute", key_func=_api_refresh_user_key)
def api_refresh():
    csrf_err = _csrf_protected_cookie_endpoint()
    if csrf_err:
        return csrf_err
    raw_rt = request.cookies.get(_RT_COOKIE)
    if not raw_rt:
        return jsonify({'error': 'Refresh token no presente'}), 401

    now = datetime.now(timezone.utc)
    h = _hash_token(raw_rt)
    tok = RefreshToken.query.filter_by(token_hash=h).first()
    if not tok:
        resp = jsonify({'error': 'Refresh token inválido'})
        _clear_rt_cookie(resp)
        return resp, 401

    exp = tok.expires_at
    if exp.tzinfo is None:
        exp = exp.replace(tzinfo=timezone.utc)

    if tok.revoked:
        if _is_rt_just_rotated(tok.id):
            resp = jsonify({'error': 'Refresh token ya rotado, reintenta'})
            _clear_rt_cookie(resp)
            return resp, 401
        try:
            RefreshToken.query.filter_by(user_id=tok.user_id, revoked=False).update(
                {'revoked': True}, synchronize_session=False,
            )
            db.session.commit()
            log_action(
                f"Posible robo de refresh token detectado. Todas las sesiones del "
                f"usuario #{tok.user_id} fueron revocadas."
            )
        except Exception:
            db.session.rollback()
        resp = jsonify({'error': 'Sesión comprometida. Vuelve a iniciar sesión.'})
        _clear_rt_cookie(resp)
        return resp, 401

    if exp <= now:
        tok.revoked = True
        db.session.commit()
        resp = jsonify({'error': 'Refresh token expirado'})
        _clear_rt_cookie(resp)
        return resp, 401

    user_id = tok.user_id

    updated = (
        db.session.query(RefreshToken)
        .filter(RefreshToken.id == tok.id, RefreshToken.revoked == False)
        .update({RefreshToken.revoked: True}, synchronize_session=False)
    )
    db.session.commit()
    if updated == 0:
        resp = jsonify({'error': 'Refresh token ya rotado'})
        _clear_rt_cookie(resp)
        return resp, 401

    _mark_rt_just_rotated(tok.id)

    user = db.session.get(User, user_id)
    if user is None:
        resp = jsonify({'error': 'Usuario no encontrado'})
        _clear_rt_cookie(resp)
        return resp, 401
    if not user.activo:
        resp = jsonify({'error': 'Cuenta desactivada'})
        _clear_rt_cookie(resp)
        return resp, 401

    new_raw = secrets.token_urlsafe(32)
    new_tok = RefreshToken(
        token_hash=_hash_token(new_raw),
        user_id=user.id,
        expires_at=now + timedelta(days=REFRESH_TOKEN_LIFETIME_DAYS),
    )
    db.session.add(new_tok)
    db.session.flush()
    RefreshToken.query.filter(
        RefreshToken.user_id == user.id,
        (RefreshToken.revoked == True) | (RefreshToken.expires_at <= now),
        RefreshToken.id != new_tok.id,
    ).delete(synchronize_session=False)
    db.session.commit()
    _store_rt_meta(new_tok.id)

    access = _encode_access_token(user)
    resp = jsonify({'token': access, 'user': _user_to_dict(user)})
    _set_rt_cookie(resp, new_raw)
    return resp


@bp.route('/logout', methods=['POST'])
def api_logout():
    csrf_err = _csrf_protected_cookie_endpoint()
    if csrf_err:
        return csrf_err

    session_closed = False

    auth_h = request.headers.get('Authorization', '')
    if auth_h.startswith('Bearer '):
        access_tok = auth_h.split(' ', 1)[1].strip()
        payload = _decode_token(access_tok, 'access')
        if payload and payload.get('jti') and payload.get('exp'):
            _revoke_jti(payload['jti'], int(payload['exp']))
            session_closed = True

    raw_rt = request.cookies.get(_RT_COOKIE)
    if raw_rt:
        h = _hash_token(raw_rt)
        tok = RefreshToken.query.filter_by(token_hash=h).first()
        if tok and not tok.revoked:
            tok.revoked = True
            try:
                db.session.commit()
            except Exception:
                db.session.rollback()
        if tok:
            session_closed = True
            user = db.session.get(User, tok.user_id)
            if user:
                g._jwt_user = user

    if session_closed:
        log_action("Logout")
    resp = jsonify({'ok': True})
    _clear_rt_cookie(resp)
    return resp
