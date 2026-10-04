from datetime import datetime, timedelta

from flask import jsonify, request

from app.extensions import db
from app.models import AuditLog
from app.routes._api_helpers import require_admin

from ._core import _log_to_dict, _log_to_dict_detalle, bp
from ..api_auth import jwt_required


@bp.route('', methods=['GET'])
@jwt_required
def listar():
    err = require_admin()
    if err:
        return err

    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 50, type=int), 200)
    usuario = (request.args.get('user') or '').strip()
    entidad = (request.args.get('entidad') or '').strip()
    origen = (request.args.get('origen') or '').strip()
    fecha = (request.args.get('fecha') or '').strip()

    query = AuditLog.query
    if usuario:
        query = query.filter(AuditLog.user.ilike(f'%{usuario}%'))
    if entidad:
        query = query.filter(AuditLog.entidad == entidad)
    if origen:
        query = query.filter(AuditLog.origen == origen)
    if fecha:
        try:
            dia = datetime.strptime(fecha, '%Y-%m-%d').date()
            inicio = datetime.combine(dia, datetime.min.time())
            fin = inicio + timedelta(days=1)
            query = query.filter(AuditLog.created_at >= inicio, AuditLog.created_at < fin)
        except ValueError:
            pass

    pagination = query.order_by(AuditLog.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False,
    )
    return jsonify({
        'items': [_log_to_dict(log) for log in pagination.items],
        'page': pagination.page,
        'per_page': pagination.per_page,
        'total': pagination.total,
        'pages': pagination.pages,
        'has_next': pagination.has_next,
        'has_prev': pagination.has_prev,
    })


@bp.route('/<int:log_id>', methods=['GET'])
@jwt_required
def detalle(log_id: int):
    err = require_admin()
    if err:
        return err
    log = db.session.get(AuditLog, log_id)
    if not log:
        return jsonify({'error': 'Registro no encontrado'}), 404
    return jsonify(_log_to_dict_detalle(log))
