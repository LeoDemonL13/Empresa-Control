from datetime import date

from flask import jsonify, request

from app.routes._api_helpers import current_user, require_admin
from app.services.reportes import datos_general
from app.utils import log_action

from ..api_auth import jwt_required
from ._core import _construir_respuesta, _validar_formato, bp


@bp.route('/general', methods=['GET'])
@jwt_required
def general():
    err = require_admin()
    if err:
        return err

    formato = _validar_formato(request.args.get('formato'))
    if not formato:
        return jsonify({'error': 'Formato inválido, usa pdf, csv o xlsx'}), 400

    columnas, filas = datos_general()
    hoy = date.today()

    log_action('Generó el reporte general de equipos', entidad='reporte')

    return _construir_respuesta(
        formato, 'Reporte general de equipos', f'{len(filas)} equipos activos · {hoy.strftime("%d/%m/%Y")}',
        columnas, filas, current_user().username, f'nexus-obsidian-reporte-general-{hoy.isoformat()}',
    )
