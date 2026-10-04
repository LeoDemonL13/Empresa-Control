from datetime import datetime, timedelta, timezone

from flask import g, jsonify, redirect, request

from app.constants import ROLE_ADMIN, ROLE_SUPER_ADMIN
from app.extensions import db, limiter
from app.models import PLATAFORMAS_SOCIALES, SocialAccount, SocialConnection, User, _now_utc
from app.realtime import emit_to_role
from app.routes._api_helpers import api_transactional, current_user, require_admin, require_super_admin
from app.services.social import credential_manager, oauth_state, orchestrator, salud, summaries
from app.services.social.config import (
    ConfiguracionFaltante,
    frontend_base_url,
    redirect_uri_para,
)
from app.services.social.errors import SocialProviderError
from app.services.social.fechas import asegurar_utc
from app.services.social.providers import proveedor_para
from app.utils import log_action

from ..api_auth import jwt_required
from ._core import COOLDOWN_SINCRONIZACION_SEGUNDOS, bp


def _obtener_conexion(plataforma):
    return SocialConnection.query.filter_by(plataforma=plataforma).first()


def _validar_plataforma(plataforma):
    return plataforma in PLATAFORMAS_SOCIALES


@bp.route('', methods=['GET'])
@jwt_required
def listar():
    err = require_admin()
    if err:
        return err
    existentes = {c.plataforma: c for c in SocialConnection.query.all()}
    return jsonify([
        salud.resumen_conexion(existentes[p]) if p in existentes else salud.conexion_vacia(p)
        for p in PLATAFORMAS_SOCIALES
    ])


@bp.route('/<plataforma>/conectar', methods=['GET'])
@jwt_required
@limiter.limit('10 per minute')
def conectar(plataforma):
    err = require_super_admin()
    if err:
        return err
    if not _validar_plataforma(plataforma):
        return jsonify({'error': 'Plataforma no soportada'}), 400

    try:
        redirect_uri = redirect_uri_para(plataforma)
        proveedor = proveedor_para(plataforma)
        code_verifier = None
        code_challenge = None
        if proveedor.usa_pkce:
            code_verifier, code_challenge = oauth_state.generar_pkce()

        estado = oauth_state.crear_estado(plataforma, current_user().id, redirect_uri, code_verifier)
        url = proveedor.build_authorize_url(estado, redirect_uri, code_challenge)
    except ConfiguracionFaltante:
        return jsonify({
            'error': f'La plataforma "{plataforma}" no tiene configuradas sus credenciales de aplicación '
                     '(variables de entorno). Revisa CONFIGURAR_REDES_SOCIALES.md.',
        }), 409

    return jsonify({'url': url})


@bp.route('/callback/<plataforma>', methods=['GET'])
@limiter.limit('30 per minute')
def callback(plataforma):
    destino_base = f'{frontend_base_url()}/redes-sociales'
    if not _validar_plataforma(plataforma):
        return redirect(f'{destino_base}?error=plataforma_no_soportada')

    if request.args.get('error'):
        return redirect(f'{destino_base}?error=autorizacion_rechazada&plataforma={plataforma}')

    codigo = request.args.get('code')
    estado_recibido = request.args.get('state')
    fila_estado = oauth_state.consumir_estado(estado_recibido, plataforma)
    if not fila_estado or not codigo:
        return redirect(f'{destino_base}?error=estado_invalido&plataforma={plataforma}')

    usuario = db.session.get(User, fila_estado.usuario_id)
    if usuario:
        g._jwt_user = usuario

    proveedor = proveedor_para(plataforma)
    try:
        datos = proveedor.exchange_code(codigo, fila_estado.redirect_uri, fila_estado.code_verifier)
    except SocialProviderError as exc:
        log_action(
            f"Falló la conexión con '{plataforma}': {exc.mensaje}",
            entidad='social_connection', entidad_id=None,
        )
        return redirect(f'{destino_base}?error=fallo_autorizacion&plataforma={plataforma}')

    conexion = _obtener_conexion(plataforma)
    if conexion is None:
        conexion = SocialConnection(plataforma=plataforma)
        db.session.add(conexion)
        db.session.commit()

    credential_manager.guardar_tokens(conexion, datos, conectado_por=usuario.username if usuario else None)

    run = orchestrator.sincronizar_conexion(
        conexion, disparado_por='manual', usuario=usuario.username if usuario else None,
    )

    emit_to_role((ROLE_SUPER_ADMIN, ROLE_ADMIN), 'conexion_social:actualizada', {'plataforma': plataforma})

    if run.estado != 'ok':
        log_action(
            f"Conectó '{plataforma}' pero la primera sincronización falló: {run.error_mensaje}",
            entidad='social_connection', entidad_id=conexion.id,
        )
        return redirect(f'{destino_base}?conectado={plataforma}&advertencia=primera_sincronizacion_fallo')

    log_action(f"Conectó '{plataforma}' mediante OAuth", entidad='social_connection', entidad_id=conexion.id)
    return redirect(f'{destino_base}?conectado={plataforma}')


@bp.route('/<plataforma>/cuentas/<int:cuenta_id>/seguimiento', methods=['PUT'])
@jwt_required
@api_transactional('Error al actualizar la cuenta')
def actualizar_seguimiento(plataforma, cuenta_id):
    err = require_super_admin()
    if err:
        return err
    cuenta = SocialAccount.query.filter_by(id=cuenta_id, plataforma=plataforma).first()
    if not cuenta:
        return jsonify({'error': 'Cuenta no encontrada'}), 404

    data = request.get_json(silent=True) or {}
    activo = bool(data.get('seguimiento_activo', True))
    cuenta.seguimiento_activo = activo
    db.session.commit()

    log_action(
        f"{'Activó' if activo else 'Desactivó'} el seguimiento de '{cuenta.nombre}' ({plataforma})",
        entidad='social_account', entidad_id=cuenta.id,
    )
    return jsonify({'ok': True})


@bp.route('/<plataforma>/sincronizar', methods=['POST'])
@jwt_required
@limiter.limit('10 per minute')
@api_transactional('Error al sincronizar la plataforma')
def sincronizar_una(plataforma):
    err = require_admin()
    if err:
        return err
    if not _validar_plataforma(plataforma):
        return jsonify({'error': 'Plataforma no soportada'}), 400

    conexion = _obtener_conexion(plataforma)
    if not conexion or not conexion.conectada():
        return jsonify({'error': 'Esa plataforma no está conectada'}), 409

    ahora = _now_utc()
    if asegurar_utc(conexion.bloqueado_hasta) and asegurar_utc(conexion.bloqueado_hasta) > ahora:
        return jsonify({'error': 'Ya hay una sincronización en curso para esta plataforma'}), 429

    conexion.bloqueado_hasta = ahora + timedelta(seconds=COOLDOWN_SINCRONIZACION_SEGUNDOS)
    db.session.commit()
    try:
        run = orchestrator.sincronizar_conexion(conexion, disparado_por='manual', usuario=current_user().username)
    finally:
        conexion.bloqueado_hasta = None
        db.session.commit()

    log_action(
        f"Sincronizó '{plataforma}' manualmente" + ('' if run.estado == 'ok' else f' (falló: {run.error_mensaje})'),
        entidad='social_connection', entidad_id=conexion.id,
    )
    emit_to_role((ROLE_SUPER_ADMIN, ROLE_ADMIN), 'conexion_social:actualizada', {'plataforma': plataforma})

    return jsonify({
        'ok': run.estado == 'ok',
        'error': run.error_mensaje,
        'conexion': salud.resumen_conexion(conexion),
    }), (200 if run.estado == 'ok' else 502)


@bp.route('/sincronizar-todas', methods=['POST'])
@jwt_required
@limiter.limit('5 per minute')
@api_transactional('Error al sincronizar las plataformas')
def sincronizar_varias():
    err = require_admin()
    if err:
        return err

    resultados = {}
    ahora = _now_utc()
    for conexion in SocialConnection.query.filter(SocialConnection.access_token_cifrado.isnot(None)).all():
        if not conexion.conectada():
            continue
        if asegurar_utc(conexion.bloqueado_hasta) and asegurar_utc(conexion.bloqueado_hasta) > ahora:
            resultados[conexion.plataforma] = {'ok': False, 'error': 'Sincronización en curso'}
            continue
        conexion.bloqueado_hasta = ahora + timedelta(seconds=COOLDOWN_SINCRONIZACION_SEGUNDOS)
        db.session.commit()
        try:
            run = orchestrator.sincronizar_conexion(conexion, disparado_por='manual', usuario=current_user().username)
        finally:
            conexion.bloqueado_hasta = None
            db.session.commit()
        resultados[conexion.plataforma] = {'ok': run.estado == 'ok', 'error': run.error_mensaje}

    log_action('Sincronizó todas las redes sociales conectadas', entidad='social_connection', entidad_id=None)
    return jsonify(resultados)


@bp.route('/<plataforma>/desconectar', methods=['POST'])
@jwt_required
@api_transactional('Error al desconectar la plataforma')
def desconectar(plataforma):
    err = require_super_admin()
    if err:
        return err
    conexion = _obtener_conexion(plataforma)
    if not conexion:
        return jsonify({'error': 'Esa plataforma no tiene una conexión guardada'}), 404

    data = request.get_json(silent=True) or {}
    purgar = bool(data.get('purgar_historico', False))

    proveedor = proveedor_para(plataforma)
    revocado = False
    if conexion.access_token_cifrado:
        revocado = proveedor.revoke(conexion.access_token_cifrado, conexion.refresh_token_cifrado)

    if purgar:
        db.session.delete(conexion)
    else:
        conexion.access_token_cifrado = None
        conexion.refresh_token_cifrado = None
        conexion.estado = 'DISCONNECTED'
        conexion.ultimo_error = None
        conexion.ultimo_error_detalle = None
        conexion.ultimo_error_tipo = None
        conexion.proxima_sincronizacion_at = None
        conexion.proximo_reintento_at = None
    db.session.commit()

    log_action(
        f"Desconectó '{plataforma}'" + (' (revocado en la plataforma)' if revocado else '')
        + (' y eliminó el histórico' if purgar else ''),
        entidad='social_connection', entidad_id=None,
    )
    emit_to_role((ROLE_SUPER_ADMIN, ROLE_ADMIN), 'conexion_social:actualizada', {'plataforma': plataforma})
    return jsonify({'ok': True, 'revocado_en_plataforma': revocado})


@bp.route('/<plataforma>/salud', methods=['GET'])
@jwt_required
def salud_conexion(plataforma):
    err = require_admin()
    if err:
        return err
    if not _validar_plataforma(plataforma):
        return jsonify({'error': 'Plataforma no soportada'}), 400
    conexion = _obtener_conexion(plataforma)
    if not conexion:
        return jsonify(salud.conexion_vacia(plataforma))
    return jsonify(salud.panel_administracion(conexion))


@bp.route('/sistema', methods=['GET'])
@jwt_required
def sistema():
    err = require_admin()
    if err:
        return err
    return jsonify(salud.estado_sistema())


@bp.route('/resumen', methods=['GET'])
@jwt_required
def resumen():
    err = require_admin()
    if err:
        return err

    plataforma = request.args.get('plataforma') or None
    if plataforma and not _validar_plataforma(plataforma):
        return jsonify({'error': 'Plataforma no soportada'}), 400

    rango = request.args.get('rango', '7d')
    if rango == 'custom':
        desde_raw = request.args.get('desde')
        hasta_raw = request.args.get('hasta')
        if not desde_raw or not hasta_raw:
            return jsonify({'error': 'Rango personalizado requiere "desde" y "hasta" en formato ISO 8601'}), 400
        try:
            desde = datetime.fromisoformat(desde_raw)
            hasta = datetime.fromisoformat(hasta_raw)
        except ValueError:
            return jsonify({'error': 'Rango personalizado inválido; usa formato ISO 8601'}), 400
        if desde.tzinfo is None:
            desde = desde.replace(tzinfo=timezone.utc)
        if hasta.tzinfo is None:
            hasta = hasta.replace(tzinfo=timezone.utc)
        if desde >= hasta:
            return jsonify({'error': '"desde" debe ser anterior a "hasta"'}), 400
    else:
        intervalo = summaries.rango_predefinido(rango)
        if not intervalo:
            return jsonify({'error': 'Rango inválido; usa 24h, 7d, 30d o custom'}), 400
        desde, hasta = intervalo

    return jsonify(summaries.obtener_resumen(desde, hasta, plataforma))
