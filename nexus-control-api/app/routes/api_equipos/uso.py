from datetime import date, timedelta

from flask import jsonify, request

from app.extensions import db
from app.models import Aplicacion, Equipo, UsoAplicacion
from app.routes._api_helpers import require_admin

from ..api_auth import jwt_required
from ._core import bp


@bp.route('/<int:equipo_id>/uso', methods=['GET'])
@jwt_required
def uso(equipo_id):
    err = require_admin()
    if err:
        return err

    equipo = db.session.get(Equipo, equipo_id)
    if not equipo or not equipo.activo:
        return jsonify({'error': 'Equipo no encontrado'}), 404

    dias = request.args.get('dias', default=7, type=int)
    dias = max(1, min(dias, 30))
    desde = date.today() - timedelta(days=dias - 1)

    filas = (
        UsoAplicacion.query
        .join(Aplicacion)
        .filter(UsoAplicacion.equipo_id == equipo_id, UsoAplicacion.fecha >= desde)
        .add_columns(Aplicacion.nombre, Aplicacion.ejecutable)
        .all()
    )

    por_app = {}
    por_dia = {}
    for fila, nombre, ejecutable in filas:
        clave_app = fila.aplicacion_id
        acumulado = por_app.setdefault(clave_app, {
            'aplicacion_id': clave_app,
            'nombre': nombre,
            'ejecutable': ejecutable,
            'segundos': 0,
            'sesiones': 0,
        })
        acumulado['segundos'] += fila.segundos or 0
        acumulado['sesiones'] += fila.sesiones or 0

        clave_dia = fila.fecha.isoformat()
        por_dia[clave_dia] = por_dia.get(clave_dia, 0) + (fila.segundos or 0)

    return jsonify({
        'desde': desde.isoformat(),
        'hasta': date.today().isoformat(),
        'por_app': sorted(por_app.values(), key=lambda x: x['segundos'], reverse=True),
        'por_dia': [{'fecha': f, 'segundos': s} for f, s in sorted(por_dia.items())],
    })
