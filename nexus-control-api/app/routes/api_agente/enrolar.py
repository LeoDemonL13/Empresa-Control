import hashlib
import secrets
from datetime import datetime, timezone

from flask import jsonify, request

from app.constants import ROLE_ADMIN, ROLE_SUPER_ADMIN
from app.extensions import db, limiter
from app.models import CodigoEnrolamiento, Equipo
from app.realtime import emit_to_role
from app.utils import log_action

from ._core import _hash_api_key, bp

_MAX_LARGO_CODIGO = 32


@bp.route('/enrolar', methods=['POST'])
@limiter.limit('10 per minute')
def enrolar():
    data = request.get_json(silent=True) or {}
    codigo = (data.get('codigo') or '').strip().upper()
    if not codigo:
        return jsonify({'error': 'El código es obligatorio'}), 400
    if len(codigo) > _MAX_LARGO_CODIGO:
        return jsonify({'error': 'Código inválido o expirado'}), 400

    codigo_hash = hashlib.sha256(codigo.encode()).hexdigest()
    registro = (
        CodigoEnrolamiento.query
        .filter_by(codigo_hash=codigo_hash, usado_at=None)
        .filter(CodigoEnrolamiento.expira_at > datetime.now(timezone.utc))
        .first()
    )
    if not registro:
        return jsonify({'error': 'Código inválido o expirado'}), 400

    equipo = db.session.get(Equipo, registro.equipo_id)
    if not equipo or not equipo.activo:
        return jsonify({'error': 'El equipo ya no está disponible'}), 400

    api_key = secrets.token_urlsafe(32)
    equipo.api_key_hash = _hash_api_key(api_key)
    equipo.api_key_prefijo = api_key[:8]
    registro.usado_at = datetime.now(timezone.utc)
    db.session.commit()

    log_action(
        f"El agente de '{equipo.nombre}' completó el enrolamiento",
        entidad='equipo', entidad_id=equipo.id, origen='agente',
    )
    emit_to_role((ROLE_SUPER_ADMIN, ROLE_ADMIN), 'equipo:estado', {'id': equipo.id})

    return jsonify({'equipo_id': equipo.id, 'nombre': equipo.nombre, 'api_key': api_key})
