from datetime import datetime, timezone

from flask import current_app, g, jsonify, request

from app.extensions import db, limiter
from app.models import RefreshToken
from app.utils import log_action

from ._core import _RT_COOKIE, _hash_token, _is_admin_user, bp
from .jwt_required import jwt_required
from .tokens import _clear_rt_cookie, _decode_token, _load_rt_meta, _revoke_jti


@bp.route('/sesiones', methods=['GET'])
@jwt_required
def api_list_sessions():
    user = g._jwt_user
    now = datetime.now(timezone.utc)
    tokens = (
        RefreshToken.query
        .filter_by(user_id=user.id, revoked=False)
        .order_by(RefreshToken.created_at.desc())
        .all()
    )
    out = []
    for t in tokens:
        exp = t.expires_at
        if exp.tzinfo is None:
            exp = exp.replace(tzinfo=timezone.utc)
        if exp <= now:
            continue
        meta = _load_rt_meta(t.id)
        out.append({
            'id': t.id,
            'created_at': t.created_at.isoformat() if t.created_at else None,
            'expires_at': exp.isoformat(),
            'user_agent': meta.get('ua') or None,
            'ip': meta.get('ip') or None,
        })
    return jsonify(out)


@bp.route('/sesiones/<int:session_id>', methods=['DELETE'])
@jwt_required
@limiter.limit("20 per minute")
def api_revoke_session(session_id: int):
    user = g._jwt_user
    tok = RefreshToken.query.filter_by(id=session_id, user_id=user.id).first()
    if not tok:
        return jsonify({'error': 'Sesión no encontrada'}), 404

    is_self = False
    raw_rt = request.cookies.get(_RT_COOKIE)
    if raw_rt:
        try:
            actual = RefreshToken.query.filter_by(token_hash=_hash_token(raw_rt)).first()
            is_self = bool(actual and actual.id == tok.id)
        except Exception:
            is_self = False

    if not tok.revoked:
        tok.revoked = True
        db.session.commit()
        log_action(f'Revocó sesión #{session_id}', entidad='sesion', entidad_id=session_id)

    if is_self:
        auth_h = request.headers.get('Authorization', '')
        if auth_h.startswith('Bearer '):
            payload = _decode_token(auth_h.split(' ', 1)[1].strip(), 'access')
            if payload and payload.get('jti') and payload.get('exp'):
                _revoke_jti(payload['jti'], int(payload['exp']))

    resp = jsonify({'ok': True, 'self': is_self})
    if is_self:
        _clear_rt_cookie(resp)
    return resp


@bp.route('/sesiones', methods=['DELETE'])
@jwt_required
@limiter.limit("10 per minute")
def api_revoke_all_sessions():
    user = g._jwt_user
    RefreshToken.query.filter_by(user_id=user.id, revoked=False).update({'revoked': True})
    user.password_version = (user.password_version or 1) + 1
    db.session.commit()
    log_action('Revocó todas sus sesiones', entidad='sesion')
    try:
        from app.realtime import force_logout_user
        force_logout_user(user.id)
    except Exception as e:
        current_app.logger.warning('force_logout_user falló en /sesiones: %s', e)
    resp = jsonify({'ok': True})
    _clear_rt_cookie(resp)
    return resp


@bp.route('/estado-seguridad', methods=['GET'])
@jwt_required
@limiter.limit("30 per minute")
def api_estado_seguridad():
    from app.extensions import get_redis

    if not _is_admin_user(g._jwt_user):
        return jsonify({'error': 'No autorizado'}), 403

    r = get_redis()
    redis_ok = False
    detalle = 'REDIS_URL no configurada'
    if r is not None:
        try:
            redis_ok = bool(r.ping())
            detalle = 'conectado' if redis_ok else 'ping sin respuesta'
        except Exception as e:
            detalle = f'error de conexión: {type(e).__name__}'

    return jsonify({
        'redis': {'ok': redis_ok, 'detalle': detalle},
        'defensas_degradadas': [] if redis_ok else [
            'Revocación inmediata de sesión por jti (el logout no mata el token hasta su exp, ≤20 min)',
            'Bloqueo escalado por intentos fallidos de contraseña',
            'Bloqueo escalado por intentos fallidos de 2FA',
            'Anti-repetición de códigos TOTP',
            'Consumo de un solo uso del stepToken de 2FA',
            'Detección de robo de refresh token',
        ],
    })
