from datetime import datetime, timezone

from flask import current_app, g, jsonify, request
from sqlalchemy.exc import IntegrityError

from app.constants import ROLE_ADMIN, ROLE_SUPER_ADMIN
from app.extensions import db, limiter
from app.realtime import emit_to_role

from ._core import agente_requerido, bp

_CAMPOS = ('hostname', 'ip', 'mac', 'sistema_operativo', 'agente_version')


@bp.route('/inventario', methods=['POST'])
@agente_requerido
@limiter.limit('30 per minute')
def inventario():
    equipo = g._equipo
    data = request.get_json(silent=True) or {}

    for campo in _CAMPOS:
        if campo in data:
            valor = (data.get(campo) or '').strip()
            setattr(equipo, campo, valor or None)

    equipo.ultimo_latido = datetime.now(timezone.utc)

    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return jsonify({'error': 'La dirección MAC ya está registrada en otro equipo'}), 409
    except Exception as e:
        db.session.rollback()
        current_app.logger.error('Error guardando inventario: %s', e)
        return jsonify({'error': 'Error al guardar el inventario'}), 500

    emit_to_role((ROLE_SUPER_ADMIN, ROLE_ADMIN), 'equipo:estado', {'id': equipo.id})
    return jsonify({'ok': True})
