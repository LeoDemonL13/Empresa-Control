from flask import jsonify

from app.extensions import db
from app.models import AppInstalada, Equipo
from app.routes._api_helpers import require_admin

from ..api_auth import jwt_required
from ._core import bp


@bp.route('/<int:equipo_id>/apps-instaladas', methods=['GET'])
@jwt_required
def listar_apps_instaladas(equipo_id):
    err = require_admin()
    if err:
        return err

    equipo = db.session.get(Equipo, equipo_id)
    if not equipo or not equipo.activo:
        return jsonify({'error': 'Equipo no encontrado'}), 404

    apps = (
        AppInstalada.query
        .filter_by(equipo_id=equipo_id)
        .order_by(AppInstalada.etiqueta.asc())
        .all()
    )
    return jsonify([{'paquete': a.paquete, 'etiqueta': a.etiqueta} for a in apps])
