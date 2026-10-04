from flask import current_app, jsonify, request
from werkzeug.security import generate_password_hash

from app.constants import ROLE_ADMIN, ROLE_SUPER_ADMIN
from app.extensions import db, limiter
from app.models import RefreshToken, User
from app.realtime import emit_to_role
from app.routes._api_helpers import api_transactional, current_user, require_super_admin
from app.utils import is_strong_password, log_action

from ._core import _ROLE_ORDER, _user_to_dict, bp
from ..api_auth import jwt_required


@bp.route('', methods=['GET'])
@jwt_required
def listar():
    err = require_super_admin()
    if err:
        return err
    users = User.query.all()
    users.sort(key=lambda u: (_ROLE_ORDER.get(u.role, 99), (u.username or '').lower()))
    return jsonify([_user_to_dict(u) for u in users])


@bp.route('', methods=['POST'])
@jwt_required
@limiter.limit('10 per minute')
@api_transactional('Error al crear el administrador')
def crear():
    err = require_super_admin()
    if err:
        return err

    data = request.get_json(silent=True) or {}
    username = (data.get('username') or '').strip()
    password = data.get('password') or ''
    full_name = (data.get('full_name') or '').strip() or None
    position = (data.get('position') or '').strip() or None
    contact_info = (data.get('contact_info') or '').strip() or None

    if not username or not password:
        return jsonify({'error': 'Usuario y contraseña son obligatorios'}), 400
    if User.query.filter_by(username=username).first():
        return jsonify({'error': 'El nombre de usuario ya existe'}), 409
    if not is_strong_password(password):
        return jsonify({
            'error': 'La contraseña es débil. Usa mínimo 12 caracteres con mayúsculas, minúsculas, números y símbolos, y que no sea una contraseña común.',
        }), 400

    nuevo = User(
        username=username,
        password_hash=generate_password_hash(password),
        role=ROLE_ADMIN,
        full_name=full_name,
        position=position,
        contact_info=contact_info,
    )
    db.session.add(nuevo)
    db.session.commit()
    log_action(f"Creó al administrador '{username}'", entidad='usuario', entidad_id=nuevo.id)
    emit_to_role((ROLE_SUPER_ADMIN, ROLE_ADMIN), 'usuario:changed', {'id': nuevo.id, 'action': 'created'})
    return jsonify(_user_to_dict(nuevo)), 201


@bp.route('/<int:user_id>', methods=['PUT'])
@jwt_required
@limiter.limit('20 per minute')
@api_transactional('Error al actualizar el administrador')
def actualizar(user_id):
    err = require_super_admin()
    if err:
        return err

    user = db.session.get(User, user_id)
    if not user:
        return jsonify({'error': 'Administrador no encontrado'}), 404

    data = request.get_json(silent=True) or {}
    for campo in ('full_name', 'position', 'contact_info'):
        if campo in data:
            valor = data.get(campo)
            setattr(user, campo, (valor or '').strip() or None)
    if 'permisos' in data:
        user.permisos = data.get('permisos')

    db.session.commit()
    log_action(f"Actualizó al administrador '{user.username}'", entidad='usuario', entidad_id=user.id)
    emit_to_role((ROLE_SUPER_ADMIN, ROLE_ADMIN), 'usuario:changed', {'id': user.id, 'action': 'updated'})
    return jsonify(_user_to_dict(user))


@bp.route('/<int:user_id>', methods=['DELETE'])
@jwt_required
def eliminar(user_id):
    err = require_super_admin()
    if err:
        return err

    if user_id == current_user().id:
        return jsonify({'error': 'No puedes desactivar tu propia cuenta'}), 400

    user = db.session.get(User, user_id)
    if not user:
        return jsonify({'error': 'Administrador no encontrado'}), 404
    if not user.activo:
        return jsonify({'error': 'La cuenta ya está desactivada'}), 400
    if user.role == ROLE_SUPER_ADMIN:
        activos_super = User.query.filter_by(role=ROLE_SUPER_ADMIN, activo=True).count()
        if activos_super <= 1:
            return jsonify({'error': 'Debe quedar al menos un súper administrador activo'}), 400

    try:
        user.activo = False
        RefreshToken.query.filter_by(user_id=user.id, revoked=False).update({'revoked': True})
        user.password_version = (user.password_version or 1) + 1
        db.session.commit()
        log_action(f"Desactivó al administrador '{user.username}'", entidad='usuario', entidad_id=user.id)
        try:
            from app.realtime import force_logout_user
            force_logout_user(user.id)
        except Exception as e:
            current_app.logger.warning('force_logout_user falló al desactivar: %s', e)
        emit_to_role((ROLE_SUPER_ADMIN, ROLE_ADMIN), 'usuario:changed', {'id': user.id, 'action': 'deactivated'})
        return jsonify({'ok': True})
    except Exception as e:
        db.session.rollback()
        current_app.logger.error('Error desactivando administrador: %s', e)
        return jsonify({'error': 'Error al desactivar al administrador'}), 500


@bp.route('/<int:user_id>/reactivar', methods=['POST'])
@jwt_required
@limiter.limit('20 per minute')
def reactivar(user_id):
    err = require_super_admin()
    if err:
        return err

    user = db.session.get(User, user_id)
    if not user:
        return jsonify({'error': 'Administrador no encontrado'}), 404
    if user.activo:
        return jsonify({'error': 'La cuenta ya está activa'}), 400

    try:
        user.activo = True
        db.session.commit()
        log_action(f"Reactivó al administrador '{user.username}'", entidad='usuario', entidad_id=user.id)
        emit_to_role((ROLE_SUPER_ADMIN, ROLE_ADMIN), 'usuario:changed', {'id': user.id, 'action': 'reactivated'})
        return jsonify(_user_to_dict(user))
    except Exception as e:
        db.session.rollback()
        current_app.logger.error('Error reactivando administrador: %s', e)
        return jsonify({'error': 'Error al reactivar al administrador'}), 500
