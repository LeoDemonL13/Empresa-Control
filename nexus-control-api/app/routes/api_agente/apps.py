from flask import current_app, g, jsonify, request

from app.extensions import db, limiter
from app.services.apps_instaladas import reemplazar_inventario

from ._core import agente_requerido, bp

_MAX_APPS = 1000


@bp.route('/apps-instaladas', methods=['POST'])
@agente_requerido
@limiter.limit('10 per minute')
def apps_instaladas():
    equipo = g._equipo
    data = request.get_json(silent=True) or {}

    apps = data.get('apps')
    if not isinstance(apps, list):
        return jsonify({'error': 'El listado de apps debe ser una lista'}), 400
    if len(apps) > _MAX_APPS:
        return jsonify({'error': f'Demasiadas apps, el máximo es {_MAX_APPS}'}), 400

    entradas = [a for a in apps if isinstance(a, dict)]

    try:
        guardadas = reemplazar_inventario(equipo.id, entradas)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        current_app.logger.error('Error guardando las apps instaladas: %s', e)
        return jsonify({'error': 'Error al guardar las apps instaladas'}), 500

    return jsonify({'ok': True, 'guardadas': guardadas})
