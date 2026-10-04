from datetime import datetime, timezone

from flask import current_app, jsonify, request

from app.constants import ROLE_ADMIN, ROLE_SUPER_ADMIN, TIPOS_EQUIPO
from app.extensions import db, limiter
from app.models import CodigoEnrolamiento, Equipo
from app.realtime import emit_to_role
from app.routes._api_helpers import api_transactional, current_user, require_admin
from app.services.categorias import obtener_o_crear
from app.utils import log_action

from ..api_auth import jwt_required
from ._core import _equipo_to_dict, bp
from .enrolamiento import _generar_codigo_enrolamiento

_CAMPOS_TEXTO = ('nombre', 'usuario_asignado', 'hostname', 'ip', 'sistema_operativo')


@bp.route('', methods=['GET'])
@jwt_required
def listar():
    err = require_admin()
    if err:
        return err

    query = Equipo.query.filter_by(activo=True)

    categoria_id = request.args.get('categoria_id', type=int)
    if categoria_id:
        query = query.filter(Equipo.categoria_id == categoria_id)

    q = (request.args.get('q') or '').strip()
    if q:
        patron = f'%{q}%'
        query = query.filter(
            db.or_(
                Equipo.nombre.ilike(patron),
                Equipo.usuario_asignado.ilike(patron),
                Equipo.hostname.ilike(patron),
            )
        )

    equipos = query.order_by(Equipo.nombre.asc()).all()
    items = [_equipo_to_dict(e) for e in equipos]

    estado = (request.args.get('estado') or '').strip()
    if estado == 'en_linea':
        items = [i for i in items if i['en_linea']]
    elif estado == 'fuera_linea':
        items = [i for i in items if not i['en_linea']]

    return jsonify(items)


@bp.route('/<int:equipo_id>', methods=['GET'])
@jwt_required
def detalle(equipo_id):
    err = require_admin()
    if err:
        return err

    equipo = db.session.get(Equipo, equipo_id)
    if not equipo or not equipo.activo:
        return jsonify({'error': 'Equipo no encontrado'}), 404

    payload = _equipo_to_dict(equipo)
    pendiente = (
        CodigoEnrolamiento.query
        .filter_by(equipo_id=equipo.id, usado_at=None)
        .filter(CodigoEnrolamiento.expira_at > datetime.now(timezone.utc))
        .order_by(CodigoEnrolamiento.created_at.desc())
        .first()
    )
    payload['codigo_pendiente'] = {'expira_at': pendiente.expira_at.isoformat()} if pendiente else None
    return jsonify(payload)


@bp.route('', methods=['POST'])
@jwt_required
@limiter.limit('20 per minute')
@api_transactional('Error al crear el equipo')
def crear():
    err = require_admin()
    if err:
        return err

    data = request.get_json(silent=True) or {}
    nombre = (data.get('nombre') or '').strip()
    if not nombre:
        return jsonify({'error': 'El nombre del equipo es obligatorio'}), 400
    if len(nombre) > 120:
        return jsonify({'error': 'El nombre es demasiado largo'}), 400

    tipo = (data.get('tipo') or TIPOS_EQUIPO[0]).strip()
    if tipo not in TIPOS_EQUIPO:
        return jsonify({'error': 'Tipo de equipo inválido'}), 400

    categoria_nombre = (data.get('categoria') or '').strip()
    categoria = None
    categoria_creada = False
    if categoria_nombre:
        categoria, categoria_creada = obtener_o_crear(categoria_nombre, current_user().username)

    equipo = Equipo(
        nombre=nombre,
        tipo=tipo,
        usuario_asignado=(data.get('usuario_asignado') or '').strip() or None,
        hostname=(data.get('hostname') or '').strip() or None,
        ip=(data.get('ip') or '').strip() or None,
        sistema_operativo=(data.get('sistema_operativo') or '').strip() or None,
        categoria=categoria,
        created_by=current_user().username,
    )
    db.session.add(equipo)
    db.session.flush()

    codigo_plano, codigo_registro = _generar_codigo_enrolamiento(equipo.id, current_user().username)
    db.session.add(codigo_registro)
    db.session.commit()

    log_action(f"Creó el equipo '{nombre}'", entidad='equipo', entidad_id=equipo.id)
    if categoria_creada:
        log_action(f"Creó la categoría '{categoria.nombre}'", entidad='categoria', entidad_id=categoria.id)
        emit_to_role((ROLE_SUPER_ADMIN, ROLE_ADMIN), 'categoria:nueva', {'id': categoria.id, 'nombre': categoria.nombre})
    emit_to_role((ROLE_SUPER_ADMIN, ROLE_ADMIN), 'equipo:alta', {'id': equipo.id, 'nombre': equipo.nombre})

    payload = _equipo_to_dict(equipo)
    payload['codigo_enrolamiento'] = codigo_plano
    payload['codigo_expira_at'] = codigo_registro.expira_at.isoformat()
    return jsonify(payload), 201


@bp.route('/<int:equipo_id>', methods=['PUT'])
@jwt_required
@limiter.limit('30 per minute')
@api_transactional('Error al actualizar el equipo')
def actualizar(equipo_id):
    err = require_admin()
    if err:
        return err

    equipo = db.session.get(Equipo, equipo_id)
    if not equipo or not equipo.activo:
        return jsonify({'error': 'Equipo no encontrado'}), 404

    data = request.get_json(silent=True) or {}
    if 'nombre' in data and not (data.get('nombre') or '').strip():
        return jsonify({'error': 'El nombre del equipo es obligatorio'}), 400

    if 'tipo' in data:
        tipo = (data.get('tipo') or '').strip()
        if tipo not in TIPOS_EQUIPO:
            return jsonify({'error': 'Tipo de equipo inválido'}), 400
        equipo.tipo = tipo

    for campo in _CAMPOS_TEXTO:
        if campo in data:
            valor = (data.get(campo) or '').strip()
            setattr(equipo, campo, valor or None)

    categoria_creada = False
    categoria_obj = None
    if 'categoria' in data:
        categoria_nombre = (data.get('categoria') or '').strip()
        if categoria_nombre:
            categoria_obj, categoria_creada = obtener_o_crear(categoria_nombre, current_user().username)
            equipo.categoria = categoria_obj
        else:
            equipo.categoria = None

    db.session.commit()
    log_action(f"Actualizó el equipo '{equipo.nombre}'", entidad='equipo', entidad_id=equipo.id)
    if categoria_creada:
        log_action(f"Creó la categoría '{categoria_obj.nombre}'", entidad='categoria', entidad_id=categoria_obj.id)
        emit_to_role((ROLE_SUPER_ADMIN, ROLE_ADMIN), 'categoria:nueva', {'id': categoria_obj.id, 'nombre': categoria_obj.nombre})
    emit_to_role((ROLE_SUPER_ADMIN, ROLE_ADMIN), 'equipo:estado', {'id': equipo.id})
    return jsonify(_equipo_to_dict(equipo))


@bp.route('/<int:equipo_id>', methods=['DELETE'])
@jwt_required
def eliminar(equipo_id):
    err = require_admin()
    if err:
        return err

    equipo = db.session.get(Equipo, equipo_id)
    if not equipo or not equipo.activo:
        return jsonify({'error': 'Equipo no encontrado'}), 404

    try:
        equipo.activo = False
        db.session.commit()
        log_action(f"Dio de baja el equipo '{equipo.nombre}'", entidad='equipo', entidad_id=equipo.id)
        emit_to_role((ROLE_SUPER_ADMIN, ROLE_ADMIN), 'equipo:estado', {'id': equipo.id, 'action': 'baja'})
        return jsonify({'ok': True})
    except Exception as e:
        db.session.rollback()
        current_app.logger.error('Error dando de baja el equipo: %s', e)
        return jsonify({'error': 'Error al dar de baja el equipo'}), 500
