import hashlib
import secrets
from datetime import datetime, timedelta, timezone

from flask import jsonify

from app.constants import ENROLAMIENTO_TTL_MINUTOS
from app.extensions import db, limiter
from app.models import CodigoEnrolamiento, Equipo
from app.routes._api_helpers import current_user, require_admin
from app.utils import log_action

from ..api_auth import jwt_required
from ._core import bp

_ALFABETO = '23456789ABCDEFGHJKLMNPQRSTUVWXYZ'


def _generar_codigo_enrolamiento(equipo_id: int, creado_por: str | None):
    crudo = ''.join(secrets.choice(_ALFABETO) for _ in range(10))
    formateado = f'{crudo[:5]}-{crudo[5:]}'
    hash_codigo = hashlib.sha256(formateado.encode()).hexdigest()
    registro = CodigoEnrolamiento(
        equipo_id=equipo_id,
        codigo_hash=hash_codigo,
        expira_at=datetime.now(timezone.utc) + timedelta(minutes=ENROLAMIENTO_TTL_MINUTOS),
        creado_por=creado_por,
    )
    return formateado, registro


@bp.route('/<int:equipo_id>/enrolamiento', methods=['POST'])
@jwt_required
@limiter.limit('10 per minute')
def regenerar_codigo(equipo_id):
    err = require_admin()
    if err:
        return err

    equipo = db.session.get(Equipo, equipo_id)
    if not equipo or not equipo.activo:
        return jsonify({'error': 'Equipo no encontrado'}), 404

    CodigoEnrolamiento.query.filter_by(equipo_id=equipo.id, usado_at=None).update({
        'expira_at': datetime.now(timezone.utc),
    })

    codigo_plano, registro = _generar_codigo_enrolamiento(equipo.id, current_user().username)
    db.session.add(registro)
    db.session.commit()

    log_action(
        f"Generó un nuevo código de enrolamiento para '{equipo.nombre}'",
        entidad='equipo', entidad_id=equipo.id,
    )

    return jsonify({
        'codigo_enrolamiento': codigo_plano,
        'codigo_expira_at': registro.expira_at.isoformat(),
    })
