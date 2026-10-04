from flask import jsonify, request

from app.constants import ROLE_ADMIN, ROLE_SUPER_ADMIN
from app.extensions import db, limiter
from app.models import ConexionRedSocial
from app.realtime import emit_to_role
from app.routes._api_helpers import api_transactional, current_user, require_admin, require_super_admin
from app.services.redes_sociales import CAMPOS_REQUERIDOS, PLATAFORMAS_SOPORTADAS
from app.services.sincronizacion_redes import sincronizar_plataforma, sincronizar_todas
from app.utils import log_action

from ..api_auth import jwt_required
from ._core import _conexion_to_dict, _conexion_vacia, bp


@bp.route('', methods=['GET'])
@jwt_required
def listar():
    err = require_admin()
    if err:
        return err

    existentes = {c.plataforma: c for c in ConexionRedSocial.query.all()}
    return jsonify([
        _conexion_to_dict(existentes[p]) if p in existentes else _conexion_vacia(p)
        for p in PLATAFORMAS_SOPORTADAS
    ])


@bp.route('/<plataforma>', methods=['PUT'])
@jwt_required
@limiter.limit('20 per minute')
@api_transactional('Error al guardar las credenciales')
def guardar(plataforma):
    err = require_super_admin()
    if err:
        return err

    if plataforma not in PLATAFORMAS_SOPORTADAS:
        return jsonify({'error': 'Plataforma no soportada'}), 400

    data = request.get_json(silent=True) or {}
    credenciales = {}
    for campo in CAMPOS_REQUERIDOS[plataforma]:
        valor = data.get(campo)
        if not isinstance(valor, str) or not valor.strip():
            return jsonify({'error': f'El campo "{campo}" es obligatorio'}), 400
        credenciales[campo] = valor.strip()

    conexion = ConexionRedSocial.query.filter_by(plataforma=plataforma).first()
    if not conexion:
        conexion = ConexionRedSocial(plataforma=plataforma)
        db.session.add(conexion)

    conexion.credenciales_cifradas = credenciales
    conexion.ultimo_error = None
    conexion.ultima_sincronizacion = None
    conexion.actualizado_por = current_user().username
    db.session.commit()

    log_action(f"Guardó las credenciales de '{plataforma}'", entidad='conexion_social', entidad_id=conexion.id)
    emit_to_role((ROLE_SUPER_ADMIN, ROLE_ADMIN), 'conexion_social:actualizada', {'plataforma': plataforma})

    return jsonify(_conexion_to_dict(conexion)), 200


@bp.route('/<plataforma>', methods=['DELETE'])
@jwt_required
@api_transactional('Error al desconectar la plataforma')
def eliminar(plataforma):
    err = require_super_admin()
    if err:
        return err

    conexion = ConexionRedSocial.query.filter_by(plataforma=plataforma).first()
    if not conexion:
        return jsonify({'error': 'Esa plataforma no tiene credenciales guardadas'}), 404

    db.session.delete(conexion)
    db.session.commit()

    log_action(f"Desconectó '{plataforma}'", entidad='conexion_social', entidad_id=None)
    emit_to_role((ROLE_SUPER_ADMIN, ROLE_ADMIN), 'conexion_social:actualizada', {'plataforma': plataforma})

    return jsonify({'ok': True})


@bp.route('/<plataforma>/sincronizar', methods=['POST'])
@jwt_required
@limiter.limit('10 per minute')
@api_transactional('Error al sincronizar la plataforma')
def sincronizar_una(plataforma):
    err = require_admin()
    if err:
        return err

    if plataforma not in PLATAFORMAS_SOPORTADAS:
        return jsonify({'error': 'Plataforma no soportada'}), 400

    ok, error = sincronizar_plataforma(plataforma)

    log_action(
        f"Sincronizó '{plataforma}' manualmente" + ('' if ok else f' (falló: {error})'),
        entidad='conexion_social', entidad_id=None,
    )

    conexion = ConexionRedSocial.query.filter_by(plataforma=plataforma).first()
    return jsonify({
        'ok': ok,
        'error': error,
        'conexion': _conexion_to_dict(conexion) if conexion else _conexion_vacia(plataforma),
    }), (200 if ok else 502)


@bp.route('/sincronizar-todas', methods=['POST'])
@jwt_required
@limiter.limit('5 per minute')
@api_transactional('Error al sincronizar las plataformas')
def sincronizar_varias():
    err = require_admin()
    if err:
        return err

    resultados = sincronizar_todas()
    log_action('Sincronizó todas las redes sociales conectadas', entidad='conexion_social', entidad_id=None)
    return jsonify(resultados)
