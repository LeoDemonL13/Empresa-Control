from __future__ import annotations

import traceback
from functools import wraps
from typing import Iterable

from flask import current_app, g, jsonify
from werkzeug.exceptions import HTTPException

from app.extensions import db
from app.models import User


def current_user() -> User:
    return g._jwt_user


def is_admin() -> bool:
    return current_user().role in ('admin', 'super_admin')


def is_super_admin() -> bool:
    return current_user().role == 'super_admin'


def require_admin(message: str = 'Acceso denegado'):
    if not is_admin():
        return jsonify({'error': message}), 403
    return None


def require_super_admin(message: str = 'Solo el súper administrador puede realizar esta acción'):
    if not is_super_admin():
        return jsonify({'error': message}), 403
    return None


def require_roles(roles: Iterable[str], message: str = 'Acceso denegado'):
    if current_user().role not in set(roles):
        return jsonify({'error': message}), 403
    return None


def api_transactional(error_message: str = 'Ocurrió un error en el servidor'):
    def wrapper(view):
        @wraps(view)
        def inner(*args, **kwargs):
            try:
                return view(*args, **kwargs)
            except HTTPException:
                raise
            except Exception as exc:
                db.session.rollback()
                current_app.logger.error(
                    '[%s] %s\n%s', view.__name__, exc, traceback.format_exc()
                )
                return jsonify({'error': error_message}), 500
        return inner
    return wrapper
