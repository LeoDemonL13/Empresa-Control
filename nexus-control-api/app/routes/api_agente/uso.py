from datetime import date, datetime

from flask import current_app, g, jsonify, request

from app.extensions import db, limiter
from app.realtime import emit_to_role
from app.constants import ROLE_ADMIN, ROLE_SUPER_ADMIN
from app.models import UsoAplicacion
from app.services.aplicaciones import obtener_o_crear as obtener_o_crear_app
from app.services.politicas import obtener_o_crear_politica

from ._core import agente_requerido, bp

_MAX_ENTRADAS = 200


@bp.route('/uso', methods=['POST'])
@agente_requerido
@limiter.limit('30 per minute')
def enviar_uso():
    equipo = g._equipo
    data = request.get_json(silent=True) or {}

    fecha_raw = (data.get('fecha') or '').strip()
    try:
        fecha = datetime.strptime(fecha_raw, '%Y-%m-%d').date()
    except ValueError:
        return jsonify({'error': 'Fecha inválida, se espera AAAA-MM-DD'}), 400
    if fecha > date.today():
        return jsonify({'error': 'La fecha no puede ser futura'}), 400

    entradas = data.get('entradas')
    if not isinstance(entradas, list):
        return jsonify({'error': 'Las entradas deben ser una lista'}), 400
    if len(entradas) > _MAX_ENTRADAS:
        return jsonify({'error': f'Demasiadas entradas, el máximo es {_MAX_ENTRADAS}'}), 400

    try:
        for entrada in entradas:
            if not isinstance(entrada, dict):
                continue
            ejecutable = (entrada.get('ejecutable') or '').strip()
            if not ejecutable:
                continue
            try:
                segundos = max(0, int(entrada.get('segundos') or 0))
                sesiones = max(0, int(entrada.get('sesiones') or 0))
            except (TypeError, ValueError):
                continue
            if segundos == 0 and sesiones == 0:
                continue

            aplicacion, _ = obtener_o_crear_app(ejecutable)
            obtener_o_crear_politica(equipo.id, aplicacion.id)

            registro = UsoAplicacion.query.filter_by(
                equipo_id=equipo.id, aplicacion_id=aplicacion.id, fecha=fecha,
            ).first()
            if registro:
                registro.segundos = (registro.segundos or 0) + segundos
                registro.sesiones = (registro.sesiones or 0) + sesiones
            else:
                db.session.add(UsoAplicacion(
                    equipo_id=equipo.id, aplicacion_id=aplicacion.id, fecha=fecha,
                    segundos=segundos, sesiones=sesiones,
                ))

        db.session.commit()
    except Exception as e:
        db.session.rollback()
        current_app.logger.error('Error guardando el uso de aplicaciones: %s', e)
        return jsonify({'error': 'Error al guardar el uso de aplicaciones'}), 500

    emit_to_role((ROLE_SUPER_ADMIN, ROLE_ADMIN), 'equipo:uso', {'id': equipo.id})
    return jsonify({'ok': True})
