from flask import jsonify

from app.extensions import db
from app.models import Categoria, Equipo
from app.routes._api_helpers import require_admin

from ..api_auth import jwt_required
from ._core import bp


@bp.route('', methods=['GET'])
@jwt_required
def listar():
    err = require_admin()
    if err:
        return err

    categorias = Categoria.query.order_by(Categoria.nombre.asc()).all()
    conteos = dict(
        db.session.query(Equipo.categoria_id, db.func.count(Equipo.id))
        .filter(Equipo.activo == True)
        .group_by(Equipo.categoria_id)
        .all()
    )
    return jsonify([
        {'id': c.id, 'nombre': c.nombre, 'total_equipos': conteos.get(c.id, 0)}
        for c in categorias
    ])
