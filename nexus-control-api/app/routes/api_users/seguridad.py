from flask import current_app, jsonify, request
from werkzeug.security import generate_password_hash

from app.extensions import db, limiter
from app.models import RefreshToken, User
from app.routes._api_helpers import current_user, require_super_admin
from app.utils import is_strong_password, log_action

from ._core import bp
from ..api_auth import jwt_required


@bp.route('/<int:user_id>/sessions', methods=['DELETE'])
@jwt_required
@limiter.limit('10 per minute')
def admin_revocar_sesiones(user_id):
    err = require_super_admin()
    if err:
        return err

    user = db.session.get(User, user_id)
    if not user:
        return jsonify({'error': 'Administrador no encontrado'}), 404

    n = RefreshToken.query.filter_by(user_id=user.id, revoked=False).update({'revoked': True})
    user.password_version = (user.password_version or 1) + 1
    db.session.commit()
    log_action(
        f"Revocó {n} sesiones del administrador '{user.username}'",
        entidad='usuario', entidad_id=user.id,
    )
    try:
        from app.realtime import force_logout_user
        force_logout_user(user.id)
    except Exception as e:
        current_app.logger.warning('force_logout_user falló: %s', e)
    return jsonify({'ok': True, 'revocadas': n})


@bp.route('/<int:user_id>/password', methods=['POST'])
@jwt_required
@limiter.limit('10 per minute')
def cambiar_password(user_id):
    err = require_super_admin()
    if err:
        return err

    user = db.session.get(User, user_id)
    if not user:
        return jsonify({'error': 'Administrador no encontrado'}), 404

    data = request.get_json(silent=True) or {}
    new_password = data.get('new_password') or ''
    if not new_password:
        return jsonify({'error': 'La contraseña no puede estar vacía'}), 400
    if not is_strong_password(new_password):
        return jsonify({
            'error': 'La contraseña nueva es débil. Usa mínimo 12 caracteres con mayúsculas, minúsculas, números y símbolos, y que no sea una contraseña común.',
        }), 400

    try:
        user.password_hash = generate_password_hash(new_password)
        user.password_version = (user.password_version or 1) + 1
        RefreshToken.query.filter_by(user_id=user.id, revoked=False).update({'revoked': True})
        db.session.commit()
        if user.id == current_user().id:
            log_action('Cambió su propia contraseña')
        else:
            log_action(f"Cambió la contraseña del administrador '{user.username}'", entidad='usuario', entidad_id=user.id)
        return jsonify({'ok': True})
    except Exception as e:
        db.session.rollback()
        current_app.logger.error('Error cambiando contraseña: %s', e)
        return jsonify({'error': 'Error al actualizar la contraseña'}), 500
