from datetime import datetime
from functools import wraps

from flask import g, jsonify, request

from app.extensions import db
from app.models import User

from .tokens import _decode_token, _is_jti_revoked


def jwt_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        auth = request.headers.get('Authorization', '')
        if not auth.startswith('Bearer '):
            return jsonify({'error': 'Token requerido'}), 401
        token = auth.split(' ', 1)[1].strip()
        payload = _decode_token(token, 'access')
        if not payload:
            return jsonify({'error': 'Token inválido o expirado'}), 401

        jti = payload.get('jti')
        if jti and _is_jti_revoked(jti):
            return jsonify({'error': 'Sesión cerrada'}), 401

        try:
            uid = int(payload['sub'])
        except (TypeError, ValueError, KeyError):
            return jsonify({'error': 'Token inválido'}), 401

        user = db.session.get(User, uid)
        if not user:
            return jsonify({'error': 'Usuario no encontrado'}), 401
        if (user.password_version or 1) != payload.get('pv', 1):
            return jsonify({'error': 'Sesión inválida, vuelve a iniciar sesión'}), 401
        if not user.activo:
            return jsonify({'error': 'Cuenta desactivada'}), 401

        try:
            now = datetime.now()
            if not user.last_seen or (now - user.last_seen).total_seconds() > 60:
                user.last_seen = now
                db.session.commit()
        except Exception:
            try:
                db.session.rollback()
            except Exception:
                pass
        g._jwt_user = user
        return fn(*args, **kwargs)

    return wrapper
