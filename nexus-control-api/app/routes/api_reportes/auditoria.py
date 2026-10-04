from datetime import datetime, timedelta, timezone

from flask import jsonify, request

from app.routes._api_helpers import current_user, require_admin
from app.services.reportes import datos_auditoria
from app.utils import log_action

from ..api_auth import jwt_required
from ._core import _construir_respuesta, _validar_formato, bp
from .uso import _parse_fecha


@bp.route('/auditoria', methods=['GET'])
@jwt_required
def auditoria():
    err = require_admin()
    if err:
        return err

    formato = _validar_formato(request.args.get('formato'))
    if not formato:
        return jsonify({'error': 'Formato inválido, usa pdf, csv o xlsx'}), 400

    hoy = datetime.now(timezone.utc).date()
    desde = _parse_fecha(request.args.get('desde'), hoy - timedelta(days=29))
    hasta = _parse_fecha(request.args.get('hasta'), hoy)
    if desde is None or hasta is None:
        return jsonify({'error': 'Fechas inválidas, se espera AAAA-MM-DD'}), 400
    if desde > hasta:
        return jsonify({'error': 'La fecha "desde" no puede ser posterior a "hasta"'}), 400

    usuario = (request.args.get('user') or '').strip() or None
    entidad = (request.args.get('entidad') or '').strip() or None
    origen = (request.args.get('origen') or '').strip() or None

    columnas, filas = datos_auditoria(desde, hasta, usuario=usuario, entidad=entidad, origen=origen)

    log_action('Generó el reporte de auditoría', entidad='reporte')

    return _construir_respuesta(
        formato, 'Reporte de auditoría',
        f'Del {desde.strftime("%d/%m/%Y")} al {hasta.strftime("%d/%m/%Y")}',
        columnas, filas, current_user().username,
        f'nexus-obsidian-reporte-auditoria-{desde.isoformat()}_{hasta.isoformat()}',
    )
