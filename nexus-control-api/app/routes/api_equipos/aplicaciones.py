from datetime import date, timedelta

from flask import current_app, jsonify, request

from app.constants import ESTADOS_APP, ROLE_ADMIN, ROLE_SUPER_ADMIN, TIPOS_USO_APP
from app.extensions import db, limiter
from app.models import Aplicacion, Equipo, EquipoAppPolitica, UsoAplicacion
from app.realtime import emit_to_equipo, emit_to_role
from app.routes._api_helpers import api_transactional, current_user, require_admin
from app.services.aplicaciones import obtener_o_crear as obtener_o_crear_app
from app.services.politicas import obtener_o_crear_politica
from app.utils import log_action

from ..api_auth import jwt_required
from ._core import bp


def _politica_to_dict(p: EquipoAppPolitica, uso_hoy: int, uso_7dias: int) -> dict:
    return {
        'id': p.id,
        'aplicacion': {
            'id': p.aplicacion.id,
            'nombre': p.aplicacion.nombre,
            'ejecutable': p.aplicacion.ejecutable,
        },
        'instalada': bool(p.instalada),
        'estado': p.estado,
        'tipo_uso': p.tipo_uso,
        'limite_minutos': p.limite_minutos,
        'periodo': p.periodo,
        'uso_hoy_segundos': uso_hoy,
        'uso_7dias_segundos': uso_7dias,
        'updated_at': p.updated_at.isoformat() if p.updated_at else None,
    }


def _mapa_uso(equipo_id: int, desde: date) -> dict:
    filas = (
        UsoAplicacion.query
        .filter(UsoAplicacion.equipo_id == equipo_id, UsoAplicacion.fecha >= desde)
        .all()
    )
    mapa = {}
    for fila in filas:
        mapa.setdefault(fila.aplicacion_id, 0)
        mapa[fila.aplicacion_id] += fila.segundos or 0
    return mapa


@bp.route('/<int:equipo_id>/aplicaciones', methods=['GET'])
@jwt_required
def listar_aplicaciones(equipo_id):
    err = require_admin()
    if err:
        return err

    equipo = db.session.get(Equipo, equipo_id)
    if not equipo or not equipo.activo:
        return jsonify({'error': 'Equipo no encontrado'}), 404

    hoy = date.today()
    hace_7dias = hoy - timedelta(days=6)
    uso_hoy_mapa = _mapa_uso(equipo_id, hoy)
    uso_7dias_mapa = _mapa_uso(equipo_id, hace_7dias)

    politicas = (
        EquipoAppPolitica.query
        .filter_by(equipo_id=equipo_id)
        .join(Aplicacion)
        .order_by(Aplicacion.nombre.asc())
        .all()
    )
    items = [
        _politica_to_dict(p, uso_hoy_mapa.get(p.aplicacion_id, 0), uso_7dias_mapa.get(p.aplicacion_id, 0))
        for p in politicas
    ]
    return jsonify(items)


@bp.route('/<int:equipo_id>/aplicaciones', methods=['POST'])
@jwt_required
@limiter.limit('30 per minute')
@api_transactional('Error al agregar la aplicación')
def agregar_aplicacion(equipo_id):
    err = require_admin()
    if err:
        return err

    equipo = db.session.get(Equipo, equipo_id)
    if not equipo or not equipo.activo:
        return jsonify({'error': 'Equipo no encontrado'}), 404

    data = request.get_json(silent=True) or {}
    ejecutable = (data.get('ejecutable') or '').strip()
    if not ejecutable:
        return jsonify({'error': 'El ejecutable es obligatorio'}), 400
    if len(ejecutable) > 150:
        return jsonify({'error': 'El nombre del ejecutable es demasiado largo'}), 400

    nombre = (data.get('nombre') or '').strip() or None

    aplicacion, _ = obtener_o_crear_app(ejecutable, nombre=nombre)

    existente = EquipoAppPolitica.query.filter_by(equipo_id=equipo_id, aplicacion_id=aplicacion.id).first()
    if existente:
        return jsonify({'error': 'Esa aplicación ya está en la lista de este equipo'}), 409

    politica, _ = obtener_o_crear_politica(equipo_id, aplicacion.id)
    politica.actualizada_por = current_user().username
    db.session.commit()

    log_action(
        f"Agregó la aplicación '{aplicacion.nombre}' al equipo '{equipo.nombre}'",
        entidad='equipo', entidad_id=equipo.id,
    )
    emit_to_role((ROLE_SUPER_ADMIN, ROLE_ADMIN), 'equipo:politica_aplicada', {'id': equipo.id})

    return jsonify(_politica_to_dict(politica, 0, 0)), 201


@bp.route('/<int:equipo_id>/aplicaciones/<int:aplicacion_id>', methods=['PUT'])
@jwt_required
@limiter.limit('60 per minute')
@api_transactional('Error al actualizar la política')
def actualizar_politica(equipo_id, aplicacion_id):
    err = require_admin()
    if err:
        return err

    equipo = db.session.get(Equipo, equipo_id)
    if not equipo or not equipo.activo:
        return jsonify({'error': 'Equipo no encontrado'}), 404

    politica = EquipoAppPolitica.query.filter_by(equipo_id=equipo_id, aplicacion_id=aplicacion_id).first()
    if not politica:
        return jsonify({'error': 'Esa aplicación no está asignada a este equipo'}), 404

    data = request.get_json(silent=True) or {}

    if 'estado' in data:
        estado = (data.get('estado') or '').strip()
        if estado not in ESTADOS_APP:
            return jsonify({'error': 'Estado inválido'}), 400
        politica.estado = estado

    if 'tipo_uso' in data:
        tipo_uso = (data.get('tipo_uso') or '').strip()
        if tipo_uso not in TIPOS_USO_APP:
            return jsonify({'error': 'Tipo de uso inválido'}), 400
        politica.tipo_uso = tipo_uso
        if tipo_uso == 'con_limite':
            limite = data.get('limite_minutos')
            try:
                limite = int(limite)
            except (TypeError, ValueError):
                limite = 0
            if limite <= 0:
                return jsonify({'error': 'Debes indicar un límite de minutos mayor a cero'}), 400
            politica.limite_minutos = limite
        else:
            politica.limite_minutos = None
    elif 'limite_minutos' in data and politica.tipo_uso == 'con_limite':
        try:
            limite = int(data.get('limite_minutos'))
        except (TypeError, ValueError):
            return jsonify({'error': 'Límite inválido'}), 400
        if limite <= 0:
            return jsonify({'error': 'Debes indicar un límite de minutos mayor a cero'}), 400
        politica.limite_minutos = limite

    politica.actualizada_por = current_user().username
    equipo.politica_version = (equipo.politica_version or 1) + 1
    db.session.commit()

    log_action(
        f"Actualizó la política de '{politica.aplicacion.nombre}' en el equipo '{equipo.nombre}'",
        entidad='equipo', entidad_id=equipo.id,
    )
    emit_to_role((ROLE_SUPER_ADMIN, ROLE_ADMIN), 'equipo:politica_aplicada', {'id': equipo.id})
    emit_to_equipo(equipo.id, 'politica:actualizar', {'politica_version': equipo.politica_version})

    hoy = date.today()
    uso_hoy = _mapa_uso(equipo_id, hoy).get(aplicacion_id, 0)
    uso_7dias = _mapa_uso(equipo_id, hoy - timedelta(days=6)).get(aplicacion_id, 0)
    return jsonify(_politica_to_dict(politica, uso_hoy, uso_7dias))


@bp.route('/<int:equipo_id>/aplicaciones/<int:aplicacion_id>', methods=['DELETE'])
@jwt_required
def quitar_aplicacion(equipo_id, aplicacion_id):
    err = require_admin()
    if err:
        return err

    equipo = db.session.get(Equipo, equipo_id)
    if not equipo or not equipo.activo:
        return jsonify({'error': 'Equipo no encontrado'}), 404

    politica = EquipoAppPolitica.query.filter_by(equipo_id=equipo_id, aplicacion_id=aplicacion_id).first()
    if not politica:
        return jsonify({'error': 'Esa aplicación no está asignada a este equipo'}), 404

    nombre_app = politica.aplicacion.nombre

    try:
        db.session.delete(politica)
        equipo.politica_version = (equipo.politica_version or 1) + 1
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        current_app.logger.error('Error quitando la aplicación: %s', e)
        return jsonify({'error': 'Error al quitar la aplicación'}), 500

    log_action(
        f"Quitó la aplicación '{nombre_app}' del equipo '{equipo.nombre}'",
        entidad='equipo', entidad_id=equipo.id,
    )
    emit_to_role((ROLE_SUPER_ADMIN, ROLE_ADMIN), 'equipo:politica_aplicada', {'id': equipo.id})
    emit_to_equipo(equipo.id, 'politica:actualizar', {'politica_version': equipo.politica_version})

    return jsonify({'ok': True})
