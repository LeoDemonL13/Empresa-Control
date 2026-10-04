import hashlib
import secrets
from functools import wraps

from flask import Blueprint, g, jsonify, request

from app.extensions import db
from app.models import Equipo

bp = Blueprint('api_agente', __name__, url_prefix='/api/agente')


def _hash_api_key(raw: str) -> str:
    return hashlib.sha256(raw.encode()).hexdigest()


def agente_requerido(fn):
    @wraps(fn)
    def envoltura(*args, **kwargs):
        try:
            device_id = int(request.headers.get('X-Device-Id', ''))
        except (TypeError, ValueError):
            return jsonify({'error': 'Credenciales de equipo inválidas'}), 401

        api_key = (request.headers.get('X-Api-Key') or '').strip()
        if not api_key or len(api_key) > 100:
            return jsonify({'error': 'Credenciales de equipo inválidas'}), 401

        equipo = db.session.get(Equipo, device_id)
        if not equipo or not equipo.activo or not equipo.api_key_hash:
            return jsonify({'error': 'Equipo no reconocido'}), 401
        if not secrets.compare_digest(_hash_api_key(api_key), equipo.api_key_hash):
            return jsonify({'error': 'Equipo no reconocido'}), 401

        g._equipo = equipo
        return fn(*args, **kwargs)

    return envoltura
