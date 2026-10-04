import pyotp
from flask import g, jsonify, request
from werkzeug.security import check_password_hash, generate_password_hash

from app.extensions import db, limiter
from app.models import AuditLog, RefreshToken
from app.utils import is_strong_password, log_action

from ._core import _MAX_PASSWORD_LEN, _MAX_TOTP_CODE_LEN, _user_to_dict, bp
from .jwt_required import jwt_required
from .tokens import _totp_code_already_used


@bp.route('/perfil', methods=['GET'])
@jwt_required
def api_perfil():
    return jsonify(_user_to_dict(g._jwt_user))


@bp.route('/perfil', methods=['PUT'])
@jwt_required
@limiter.limit('15 per minute')
def api_actualizar_perfil():
    user = g._jwt_user
    data = request.get_json(silent=True) or {}
    for campo in ('full_name', 'position', 'contact_info'):
        if campo in data:
            valor = data.get(campo)
            setattr(user, campo, (valor or '').strip() or None)
    db.session.commit()
    log_action('Actualizó su perfil')
    return jsonify(_user_to_dict(user))


@bp.route('/perfil/actividad', methods=['GET'])
@jwt_required
def api_perfil_actividad():
    user = g._jwt_user
    try:
        limit = int(request.args.get('limit') or 20)
    except (TypeError, ValueError):
        limit = 20
    limit = max(1, min(limit, 50))
    rows = (
        AuditLog.query
        .filter(AuditLog.user == user.username)
        .order_by(AuditLog.created_at.desc())
        .limit(limit)
        .all()
    )
    return jsonify([
        {
            'id': r.id,
            'action': r.action,
            'ip': r.ip,
            'created_at': r.created_at.isoformat() if r.created_at else None,
        }
        for r in rows
    ])


@bp.route('/perfil/password', methods=['PUT'])
@jwt_required
@limiter.limit('10 per minute')
def api_cambiar_password_propia():
    user = g._jwt_user
    data = request.get_json(silent=True) or {}
    current_password = data.get('current_password') or ''
    new_password = data.get('new_password') or ''
    totp_code = (data.get('code') or '').strip()

    if not current_password or not new_password:
        return jsonify({'error': 'Contraseña actual y nueva son obligatorias'}), 400
    if len(current_password) > _MAX_PASSWORD_LEN or len(new_password) > _MAX_PASSWORD_LEN:
        return jsonify({'error': 'Contraseña excede la longitud permitida'}), 400
    if not check_password_hash(user.password_hash, current_password):
        return jsonify({'error': 'La contraseña actual es incorrecta'}), 401

    if user.totp_secret:
        if not totp_code:
            return jsonify({
                'error': 'Se requiere código 2FA para cambiar la contraseña',
                'requires_totp': True,
            }), 401
        if len(totp_code) > _MAX_TOTP_CODE_LEN:
            return jsonify({'error': 'Código 2FA inválido'}), 401
        if not pyotp.TOTP(user.totp_secret).verify(totp_code, valid_window=1):
            return jsonify({'error': 'Código 2FA incorrecto'}), 401
        if _totp_code_already_used(user.id, totp_code):
            return jsonify({'error': 'Ese código ya fue usado. Espera al siguiente.'}), 401

    if not is_strong_password(new_password):
        return jsonify({
            'error': 'La contraseña nueva es débil. Mínimo 12 caracteres con mayúsculas, minúsculas, números y símbolos, y que no sea una contraseña común.',
        }), 400
    if current_password == new_password:
        return jsonify({'error': 'La nueva contraseña debe ser diferente a la actual'}), 400

    user.password_hash = generate_password_hash(new_password)
    user.password_version = (user.password_version or 1) + 1
    RefreshToken.query.filter_by(user_id=user.id, revoked=False).update({'revoked': True})
    db.session.commit()
    log_action('Cambió su contraseña')
    return jsonify({'ok': True})
