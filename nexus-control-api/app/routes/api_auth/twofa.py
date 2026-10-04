import hashlib as _h
import secrets
from datetime import datetime, timezone

import pyotp
from flask import current_app, g, jsonify, request
from werkzeug.security import check_password_hash

from app.extensions import db, limiter
from app.models import RefreshToken, TwoFactorBackupCode
from app.utils import log_action

from ._core import (
    _BACKUP_CODES_COUNT,
    _BACKUP_CODES_LOW_THRESHOLD,
    _LOCKOUT_DURATIONS,
    _LOCKOUT_LEVEL_TTL,
    _LOGIN_FAILS_THRESHOLD,
    _LOGIN_FAILS_WINDOW,
    _MAX_PASSWORD_LEN,
    _MAX_TOTP_CODE_LEN,
    _SETUP_2FA_TTL,
    bp,
)
from .jwt_required import jwt_required
from .tokens import _totp_code_already_used

_BACKUP_CODE_ALPHABET = '23456789ABCDEFGHJKLMNPQRSTUVWXYZ'


def _hash_backup_code(code: str) -> str:
    normalized = code.upper().replace('-', '').replace(' ', '')
    return _h.sha256(normalized.encode()).hexdigest()


def _format_backup_code(raw_chars: str) -> str:
    return f'{raw_chars[:4]}-{raw_chars[4:8]}-{raw_chars[8:12]}'


def _generate_backup_codes(user_id: int) -> list[str]:
    TwoFactorBackupCode.query.filter_by(user_id=user_id).delete()
    plaintexts = []
    for _ in range(_BACKUP_CODES_COUNT):
        raw = ''.join(secrets.choice(_BACKUP_CODE_ALPHABET) for _ in range(12))
        formatted = _format_backup_code(raw)
        plaintexts.append(formatted)
        db.session.add(TwoFactorBackupCode(
            user_id=user_id,
            code_hash=_hash_backup_code(formatted),
        ))
    db.session.commit()
    return plaintexts


def _count_active_backup_codes(user_id: int) -> int:
    return TwoFactorBackupCode.query.filter_by(
        user_id=user_id, consumed_at=None,
    ).count()


def _try_consume_backup_code(user_id: int, code: str) -> bool:
    if not code:
        return False
    h = _hash_backup_code(code)
    tok = TwoFactorBackupCode.query.filter_by(
        user_id=user_id, code_hash=h, consumed_at=None,
    ).first()
    if not tok:
        return False
    tok.consumed_at = datetime.now(timezone.utc)
    db.session.commit()
    return True


def _twofa_lockout_key(user_id: int) -> str:
    return f'twofa_lockout:{user_id}'


def _twofa_level_key(user_id: int) -> str:
    return f'twofa_lockout_level:{user_id}'


def _twofa_fails_key(user_id: int) -> str:
    return f'twofa_fails:{user_id}'


def _check_twofa_lockout(user_id: int):
    from app.extensions import redis_call
    ttl = redis_call(lambda r: r.ttl(_twofa_lockout_key(user_id)))
    return ttl if (ttl is not None and ttl > 0) else None


def _register_twofa_failure(user_id: int) -> None:
    from app.extensions import redis_call

    def _registrar(r):
        fkey = _twofa_fails_key(user_id)
        fails = r.incr(fkey)
        if fails == 1:
            r.expire(fkey, _LOGIN_FAILS_WINDOW)
        if fails >= _LOGIN_FAILS_THRESHOLD:
            lkey = _twofa_level_key(user_id)
            try:
                level = int(r.get(lkey) or 0)
            except (TypeError, ValueError):
                level = 0
            duration = _LOCKOUT_DURATIONS[min(level, len(_LOCKOUT_DURATIONS) - 1)]
            r.setex(_twofa_lockout_key(user_id), duration, '1')
            r.setex(lkey, _LOCKOUT_LEVEL_TTL, level + 1)
            r.delete(fkey)

    redis_call(_registrar)


def _clear_twofa_failures(user_id: int) -> None:
    from app.extensions import redis_call
    redis_call(lambda r: r.delete(
        _twofa_fails_key(user_id), _twofa_lockout_key(user_id), _twofa_level_key(user_id),
    ))


def _setup_2fa_key(user_id: int) -> str:
    return f'totp_setup_secret:{user_id}'


def _pin_setup_2fa_secret(user_id: int, secret: str) -> bool:
    from app.extensions import redis_call

    def _pinear(r):
        r.setex(_setup_2fa_key(user_id), _SETUP_2FA_TTL, secret)
        return True

    return bool(redis_call(_pinear, default=False))


def _peek_setup_2fa_secret(user_id: int) -> str | None:
    from app.extensions import redis_call
    return redis_call(lambda r: r.get(_setup_2fa_key(user_id)), default=None)


def _delete_setup_2fa_secret(user_id: int) -> None:
    from app.extensions import redis_call
    redis_call(lambda r: r.delete(_setup_2fa_key(user_id)))


@bp.route('/setup-2fa', methods=['POST'])
@jwt_required
@limiter.limit('4 per minute')
def api_setup_2fa():
    import base64
    import io as _io

    import qrcode

    user = g._jwt_user
    data = request.get_json(silent=True) or {}
    current_password = data.get('current_password') or data.get('currentPassword') or ''
    if not current_password:
        return jsonify({'error': 'Contraseña actual requerida'}), 400
    if len(current_password) > _MAX_PASSWORD_LEN:
        return jsonify({'error': 'La contraseña actual es incorrecta'}), 401
    if not check_password_hash(user.password_hash, current_password):
        return jsonify({'error': 'La contraseña actual es incorrecta'}), 401

    secret = pyotp.random_base32()
    if not _pin_setup_2fa_secret(user.id, secret):
        current_app.logger.error(
            'setup-2fa: Redis no disponible para pinear el secret. Rechazando.'
        )
        return jsonify({
            'error': 'No se puede iniciar la configuración de 2FA en este momento. Intenta más tarde.',
        }), 503
    totp_uri = pyotp.totp.TOTP(secret).provisioning_uri(
        name=user.username,
        issuer_name='Nexus Obsidian Control',
    )
    img = qrcode.make(totp_uri)
    buffered = _io.BytesIO()
    img.save(buffered, format='PNG')
    qr_b64 = base64.b64encode(buffered.getvalue()).decode('utf-8')
    return jsonify({'secret': secret, 'qr': qr_b64})


@bp.route('/confirm-2fa', methods=['POST'])
@jwt_required
@limiter.limit('6 per minute')
def api_confirm_2fa():
    user = g._jwt_user
    data = request.get_json(silent=True) or {}
    current_password = data.get('current_password') or data.get('currentPassword') or ''
    secret = data.get('secret') or ''
    code = (data.get('code') or '').strip()
    current_2fa_code = (data.get('current_2fa_code') or data.get('currentTwoFaCode') or '').strip()

    if not current_password or not secret or not code:
        return jsonify({'error': 'Faltan datos (contraseña, secret o código)'}), 400
    if len(current_password) > _MAX_PASSWORD_LEN:
        return jsonify({'error': 'La contraseña actual es incorrecta'}), 401
    if len(code) > _MAX_TOTP_CODE_LEN or len(current_2fa_code) > _MAX_TOTP_CODE_LEN:
        return jsonify({'error': 'Código inválido'}), 400
    if len(secret) > 64:
        return jsonify({'error': 'Secret inválido'}), 400
    if not check_password_hash(user.password_hash, current_password):
        return jsonify({'error': 'La contraseña actual es incorrecta'}), 401

    pinned = _peek_setup_2fa_secret(user.id)
    if pinned is None:
        return jsonify({
            'error': 'La configuración de 2FA expiró. Vuelve a escanear el código QR.',
        }), 400
    if not secrets.compare_digest(pinned, secret):
        log_action(f"2FA confirm: secret no coincide con el pineado para {user.username}")
        return jsonify({
            'error': 'El secret no coincide con el de la configuración. Vuelve a escanear el código QR.',
        }), 400

    if user.totp_secret:
        if not current_2fa_code:
            return jsonify({
                'error': 'Ya tienes 2FA activo. Para cambiar de dispositivo necesitas el código actual.',
                'requires_current_2fa_code': True,
            }), 401
        if not pyotp.TOTP(user.totp_secret).verify(current_2fa_code, valid_window=1):
            log_action(f"2FA re-key: código actual incorrecto para {user.username}")
            return jsonify({'error': 'Código 2FA actual incorrecto'}), 401
        if _totp_code_already_used(user.id, current_2fa_code):
            return jsonify({'error': 'Ese código ya fue usado. Espera al siguiente.'}), 401

    if not pyotp.TOTP(secret).verify(code, valid_window=1):
        log_action(f"2FA setup: código incorrecto para {user.username}")
        return jsonify({'error': 'Código incorrecto'}), 400

    try:
        user.totp_secret = secret
        RefreshToken.query.filter_by(user_id=user.id, revoked=False).update({'revoked': True})
        db.session.commit()
        _delete_setup_2fa_secret(user.id)
        log_action(f"2FA activado para {user.username}", entidad='usuario', entidad_id=user.id)
        return jsonify({'ok': True})
    except Exception as e:
        db.session.rollback()
        current_app.logger.error('Error guardando totp_secret: %s', e)
        return jsonify({'error': 'Error al activar 2FA'}), 500


@bp.route('/disable-2fa', methods=['POST'])
@jwt_required
@limiter.limit('4 per minute')
def api_disable_2fa():
    user = g._jwt_user
    data = request.get_json(silent=True) or {}
    current_password = data.get('current_password') or data.get('currentPassword') or ''
    code = (data.get('code') or '').strip()

    if not user.totp_secret:
        return jsonify({'error': '2FA no está activo en esta cuenta'}), 400
    if not current_password or not code:
        return jsonify({'error': 'Contraseña actual y código 2FA son obligatorios'}), 400
    if len(current_password) > _MAX_PASSWORD_LEN or len(code) > _MAX_TOTP_CODE_LEN:
        return jsonify({'error': 'Credenciales incorrectas'}), 401
    if not check_password_hash(user.password_hash, current_password):
        return jsonify({'error': 'La contraseña actual es incorrecta'}), 401
    if not pyotp.TOTP(user.totp_secret).verify(code, valid_window=1):
        log_action(f"2FA disable: código incorrecto para {user.username}")
        return jsonify({'error': 'Código 2FA incorrecto'}), 401
    if _totp_code_already_used(user.id, code):
        return jsonify({'error': 'Ese código ya fue usado. Espera al siguiente.'}), 401

    try:
        user.totp_secret = None
        RefreshToken.query.filter_by(user_id=user.id, revoked=False).update({'revoked': True})
        TwoFactorBackupCode.query.filter_by(user_id=user.id).delete()
        db.session.commit()
        log_action(f"2FA desactivado para {user.username}", entidad='usuario', entidad_id=user.id)
        return jsonify({'ok': True})
    except Exception as e:
        db.session.rollback()
        current_app.logger.error('Error desactivando 2FA: %s', e)
        return jsonify({'error': 'Error al desactivar 2FA'}), 500


@bp.route('/backup-codes', methods=['GET'])
@jwt_required
def api_backup_codes_status():
    user = g._jwt_user
    if not user.totp_secret:
        return jsonify({'enabled': False, 'remaining': 0})
    remaining = _count_active_backup_codes(user.id)
    return jsonify({
        'enabled': True,
        'remaining': remaining,
        'low': remaining <= _BACKUP_CODES_LOW_THRESHOLD,
    })


@bp.route('/backup-codes', methods=['POST'])
@jwt_required
@limiter.limit('4 per minute')
def api_generate_backup_codes():
    user = g._jwt_user
    data = request.get_json(silent=True) or {}
    current_password = data.get('current_password') or data.get('currentPassword') or ''
    code = (data.get('code') or '').strip()

    if not user.totp_secret:
        return jsonify({'error': '2FA no está activo. Actívalo primero.'}), 400
    if not current_password or not code:
        return jsonify({'error': 'Contraseña actual y código 2FA son obligatorios'}), 400
    if len(current_password) > _MAX_PASSWORD_LEN or len(code) > _MAX_TOTP_CODE_LEN:
        return jsonify({'error': 'Credenciales incorrectas'}), 401
    if not check_password_hash(user.password_hash, current_password):
        return jsonify({'error': 'La contraseña actual es incorrecta'}), 401
    if not pyotp.TOTP(user.totp_secret).verify(code, valid_window=1):
        log_action(f"backup-codes: código TOTP incorrecto para {user.username}")
        return jsonify({'error': 'Código 2FA incorrecto'}), 401
    if _totp_code_already_used(user.id, code):
        return jsonify({'error': 'Ese código ya fue usado. Espera al siguiente.'}), 401

    try:
        codes = _generate_backup_codes(user.id)
        log_action(f"Backup codes regenerados ({len(codes)}) para {user.username}", entidad='usuario', entidad_id=user.id)
        return jsonify({
            'codes': codes,
            'count': len(codes),
            'warning': (
                'Estos códigos se muestran UNA SOLA VEZ. Guárdalos en un lugar '
                'seguro. Cada código solo se puede usar una vez. Regenerar '
                'invalida los anteriores.'
            ),
        })
    except Exception as e:
        db.session.rollback()
        current_app.logger.error('Error generando backup codes: %s', e)
        return jsonify({'error': 'Error al generar códigos de respaldo'}), 500


@bp.route('/backup-codes', methods=['DELETE'])
@jwt_required
@limiter.limit('4 per minute')
def api_revoke_backup_codes():
    user = g._jwt_user
    data = request.get_json(silent=True) or {}
    current_password = data.get('current_password') or data.get('currentPassword') or ''
    code = (data.get('code') or '').strip()

    if not user.totp_secret:
        return jsonify({'error': '2FA no está activo'}), 400
    if not current_password or not code:
        return jsonify({'error': 'Contraseña actual y código 2FA son obligatorios'}), 400
    if len(current_password) > _MAX_PASSWORD_LEN or len(code) > _MAX_TOTP_CODE_LEN:
        return jsonify({'error': 'Credenciales incorrectas'}), 401
    if not check_password_hash(user.password_hash, current_password):
        return jsonify({'error': 'La contraseña actual es incorrecta'}), 401
    if not pyotp.TOTP(user.totp_secret).verify(code, valid_window=1):
        return jsonify({'error': 'Código 2FA incorrecto'}), 401
    if _totp_code_already_used(user.id, code):
        return jsonify({'error': 'Ese código ya fue usado. Espera al siguiente.'}), 401

    n = TwoFactorBackupCode.query.filter_by(user_id=user.id).delete()
    db.session.commit()
    log_action(f"Backup codes revocados ({n}) para {user.username}", entidad='usuario', entidad_id=user.id)
    return jsonify({'ok': True, 'revocados': n})
