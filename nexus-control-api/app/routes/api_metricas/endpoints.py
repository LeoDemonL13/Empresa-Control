from flask import jsonify, request

from app.constants import ROLE_ADMIN, ROLE_SUPER_ADMIN
from app.extensions import db, limiter
from app.models import MetricaSocial
from app.realtime import emit_to_role
from app.routes._api_helpers import api_transactional, current_user, require_admin
from app.services.metricas_sociales import obtener_o_crear
from app.utils import log_action

from ..api_auth import jwt_required
from ._core import _metrica_to_dict, bp

_CAMPOS_NUMERICOS = ('me_gusta', 'interacciones', 'impresiones')


def _parse_entero_no_negativo(valor):
    try:
        n = int(valor)
    except (TypeError, ValueError):
        return None
    return n if n >= 0 else None


def _parse_engagement(valor):
    try:
        n = float(valor)
    except (TypeError, ValueError):
        return None
    if n < 0 or n > 100:
        return None
    return n


@bp.route('', methods=['GET'])
@jwt_required
def listar():
    err = require_admin()
    if err:
        return err

    metricas = MetricaSocial.query.order_by(MetricaSocial.red_social.asc()).all()
    return jsonify([_metrica_to_dict(m) for m in metricas])


@bp.route('', methods=['POST'])
@jwt_required
@limiter.limit('30 per minute')
@api_transactional('Error al guardar las métricas')
def guardar():
    err = require_admin()
    if err:
        return err

    data = request.get_json(silent=True) or {}
    red_social = (data.get('red_social') or '').strip()
    if not red_social:
        return jsonify({'error': 'El nombre de la red social es obligatorio'}), 400
    if len(red_social) > 60:
        return jsonify({'error': 'El nombre de la red social es demasiado largo'}), 400

    metrica, _ = obtener_o_crear(red_social)

    for campo in _CAMPOS_NUMERICOS:
        if campo in data:
            valor = _parse_entero_no_negativo(data.get(campo))
            if valor is None:
                return jsonify({'error': f'El campo {campo} debe ser un número entero mayor o igual a cero'}), 400
            setattr(metrica, campo, valor)

    if 'engagement' in data:
        valor = _parse_engagement(data.get('engagement'))
        if valor is None:
            return jsonify({'error': 'El engagement debe ser un porcentaje entre 0 y 100'}), 400
        metrica.engagement = valor

    metrica.origen = 'manual'
    metrica.actualizado_por = current_user().username
    db.session.commit()

    log_action(
        f"Actualizó las métricas de '{metrica.red_social}'",
        entidad='metrica_social', entidad_id=metrica.id,
    )
    emit_to_role((ROLE_SUPER_ADMIN, ROLE_ADMIN), 'metrica:actualizada', {'id': metrica.id})

    return jsonify(_metrica_to_dict(metrica)), 201


@bp.route('/<int:metrica_id>', methods=['DELETE'])
@jwt_required
def eliminar(metrica_id):
    err = require_admin()
    if err:
        return err

    metrica = db.session.get(MetricaSocial, metrica_id)
    if not metrica:
        return jsonify({'error': 'Registro no encontrado'}), 404

    nombre = metrica.red_social
    db.session.delete(metrica)
    db.session.commit()

    log_action(f"Quitó las métricas de '{nombre}'", entidad='metrica_social', entidad_id=metrica_id)
    emit_to_role((ROLE_SUPER_ADMIN, ROLE_ADMIN), 'metrica:actualizada', {'id': metrica_id})

    return jsonify({'ok': True})
