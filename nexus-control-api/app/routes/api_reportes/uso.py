from datetime import date, datetime, timedelta

from flask import jsonify, request

from app.routes._api_helpers import current_user, require_admin
from app.services.reportes import datos_uso
from app.utils import log_action

from ..api_auth import jwt_required
from ._core import _construir_respuesta, _validar_formato, bp


def _parse_fecha(valor, default):
    if not valor:
        return default
    try:
        return datetime.strptime(valor, '%Y-%m-%d').date()
    except ValueError:
        return None


@bp.route('/uso', methods=['GET'])
@jwt_required
def uso():
    err = require_admin()
    if err:
        return err

    formato = _validar_formato(request.args.get('formato'))
    if not formato:
        return jsonify({'error': 'Formato inválido, usa pdf, csv o xlsx'}), 400

    hoy = date.today()
    desde = _parse_fecha(request.args.get('desde'), hoy - timedelta(days=6))
    hasta = _parse_fecha(request.args.get('hasta'), hoy)
    if desde is None or hasta is None:
        return jsonify({'error': 'Fechas inválidas, se espera AAAA-MM-DD'}), 400
    if desde > hasta:
        return jsonify({'error': 'La fecha "desde" no puede ser posterior a "hasta"'}), 400

    equipo_id = request.args.get('equipo_id', type=int)
    categoria_id = request.args.get('categoria_id', type=int)

    columnas, filas = datos_uso(desde, hasta, equipo_id=equipo_id, categoria_id=categoria_id)

    log_action('Generó el reporte de actividades y uso', entidad='reporte')

    return _construir_respuesta(
        formato, 'Reporte de actividades y uso',
        f'Del {desde.strftime("%d/%m/%Y")} al {hasta.strftime("%d/%m/%Y")}',
        columnas, filas, current_user().username,
        f'nexus-obsidian-reporte-uso-{desde.isoformat()}_{hasta.isoformat()}',
    )
