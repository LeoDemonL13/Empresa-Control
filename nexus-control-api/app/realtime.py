from __future__ import annotations

import logging
import os

from flask_socketio import SocketIO

from app.constants import ROLE_ADMIN, ROLE_SUPER_ADMIN

socketio = SocketIO()
_logger = logging.getLogger(__name__)
_hooks_registered = False


def init_socketio(app) -> SocketIO:
    cors_origins = [
        o.strip()
        for o in os.environ.get(
            'CORS_ORIGINS', 'http://localhost:5173,http://127.0.0.1:5173'
        ).split(',')
        if o.strip()
    ]
    redis_url = os.environ.get('REDIS_URL')
    use_message_queue = os.environ.get('SOCKETIO_MESSAGE_QUEUE', 'true').lower() != 'false'
    message_queue = redis_url if (use_message_queue and redis_url and not redis_url.startswith('memory://')) else None
    async_mode = os.environ.get('SOCKETIO_ASYNC_MODE', 'threading')
    socketio.init_app(
        app,
        cors_allowed_origins=cors_origins,
        async_mode=async_mode,
        message_queue=message_queue,
        ping_interval=25,
        ping_timeout=60,
        manage_session=False,
        logger=False,
        engineio_logger=False,
    )
    _register_audit_emit_hook()
    _register_handlers()
    _iniciar_tareas_de_fondo(app)
    return socketio


def _register_audit_emit_hook() -> None:
    global _hooks_registered
    if _hooks_registered:
        return
    _hooks_registered = True

    from sqlalchemy import event

    from app.extensions import db
    from app.models import AuditLog

    @event.listens_for(AuditLog, 'after_insert')
    def _stash_audit(mapper, connection, target):
        try:
            bucket = db.session.info.setdefault('_pending_audit_emits', [])
            bucket.append({
                'id': target.id,
                'user': target.user,
                'action': target.action,
                'entidad': target.entidad,
                'entidad_id': target.entidad_id,
                'origen': target.origen,
                'ip': target.ip,
                'created_at': target.created_at.isoformat() if target.created_at else None,
            })
        except Exception:
            pass

    @event.listens_for(db.session, 'after_commit')
    def _flush_audit_emits(session):
        bucket = session.info.pop('_pending_audit_emits', None)
        if not bucket:
            return
        for snap in bucket:
            emit_to_role((ROLE_SUPER_ADMIN, ROLE_ADMIN), 'bitacora:nuevo', snap)

    @event.listens_for(db.session, 'after_rollback')
    def _discard_audit_emits(session):
        session.info.pop('_pending_audit_emits', None)


def _register_handlers() -> None:
    from flask import request
    from flask_socketio import ConnectionRefusedError, join_room

    @socketio.on('connect')
    def _on_connect(auth):
        from app.extensions import db
        from app.models import User
        from app.routes.api_auth import _decode_token, _is_jti_revoked

        token = (auth or {}).get('token') if isinstance(auth, dict) else None
        if not token:
            _logger.info('socket: rechazado (sin token) sid=%s', request.sid)
            raise ConnectionRefusedError('token_missing')

        payload = _decode_token(token, 'access')
        if not payload:
            raise ConnectionRefusedError('token_expired')

        jti = payload.get('jti')
        if jti and _is_jti_revoked(jti):
            raise ConnectionRefusedError('token_revoked')

        try:
            user_id = int(payload['sub'])
        except (KeyError, TypeError, ValueError):
            raise ConnectionRefusedError('token_invalid')

        user = db.session.get(User, user_id)
        if not user:
            raise ConnectionRefusedError('user_not_found')
        if (user.password_version or 1) != payload.get('pv', 1):
            raise ConnectionRefusedError('token_revoked')
        if not user.activo:
            raise ConnectionRefusedError('user_inactive')

        join_room(f'user:{user.id}')
        role_name = (user.role or '').lower()
        if role_name:
            join_room(f'role:{role_name}')

        try:
            from datetime import datetime
            user.last_seen = datetime.now()
            db.session.commit()
        except Exception:
            try:
                db.session.rollback()
            except Exception:
                pass
        _logger.debug('socket: conectado sid=%s user_id=%s role=%s', request.sid, user.id, role_name)
        return True

    @socketio.on('disconnect')
    def _on_disconnect():
        _logger.debug('socket: desconectado sid=%s', request.sid)

    @socketio.on('connect', namespace='/agent')
    def _on_agent_connect(auth):
        from app.extensions import db
        from app.models import Equipo
        from app.routes.api_agente._core import _hash_api_key

        datos = auth if isinstance(auth, dict) else {}
        try:
            equipo_id = int(datos.get('device_id'))
        except (TypeError, ValueError):
            raise ConnectionRefusedError('device_id_invalido')

        api_key = (datos.get('api_key') or '').strip()
        if not api_key:
            raise ConnectionRefusedError('api_key_requerida')

        equipo = db.session.get(Equipo, equipo_id)
        if not equipo or not equipo.activo or not equipo.api_key_hash:
            raise ConnectionRefusedError('equipo_no_enrolado')

        import secrets as _secrets
        if not _secrets.compare_digest(_hash_api_key(api_key), equipo.api_key_hash):
            raise ConnectionRefusedError('credenciales_invalidas')

        _agent_sessions[request.sid] = equipo.id
        join_room(f'device:{equipo.id}', namespace='/agent')
        _logger.debug('socket/agent: conectado sid=%s equipo_id=%s', request.sid, equipo.id)
        return True

    @socketio.on('heartbeat', namespace='/agent')
    def _on_agent_heartbeat(data=None):
        from datetime import datetime, timezone

        from app.extensions import db
        from app.models import Equipo
        from app.routes.api_equipos._core import _esta_en_linea

        equipo_id = _agent_sessions.get(request.sid)
        if not equipo_id:
            return

        equipo = db.session.get(Equipo, equipo_id)
        if not equipo:
            return

        estaba_en_linea = _esta_en_linea(equipo)
        equipo.ultimo_latido = datetime.now(timezone.utc)
        try:
            db.session.commit()
        except Exception:
            db.session.rollback()
            return

        _estado_conocido[equipo.id] = True
        if not estaba_en_linea:
            emit_to_role((ROLE_SUPER_ADMIN, ROLE_ADMIN), 'equipo:estado', {'id': equipo.id})

    @socketio.on('disconnect', namespace='/agent')
    def _on_agent_disconnect():
        _agent_sessions.pop(request.sid, None)
        _logger.debug('socket/agent: desconectado sid=%s', request.sid)


_agent_sessions: dict[str, int] = {}
_estado_conocido: dict[int, bool] = {}


def _revisar_estado_equipos() -> None:
    from app.models import Equipo
    from app.routes.api_equipos._core import _esta_en_linea

    equipos = Equipo.query.filter_by(activo=True).all()
    actual = {e.id: _esta_en_linea(e) for e in equipos}

    for equipo_id, en_linea in actual.items():
        anterior = _estado_conocido.get(equipo_id)
        if anterior is not None and anterior != en_linea:
            emit_to_role((ROLE_SUPER_ADMIN, ROLE_ADMIN), 'equipo:estado', {'id': equipo_id})

    for equipo_id in set(_estado_conocido) - set(actual):
        _estado_conocido.pop(equipo_id, None)

    _estado_conocido.update(actual)


_barredor_iniciado = False


def _iniciar_tareas_de_fondo(app) -> None:
    global _barredor_iniciado
    if _barredor_iniciado or app.config.get('TESTING'):
        return
    _barredor_iniciado = True

    def _tarea():
        with app.app_context():
            while True:
                socketio.sleep(20)
                try:
                    _revisar_estado_equipos()
                except Exception as e:
                    _logger.warning('barredor de estado falló: %s', e)
                finally:
                    from app.extensions import db
                    db.session.remove()

    socketio.start_background_task(_tarea)


def force_logout_user(user_id: int) -> None:
    try:
        socketio.emit('auth:forzar_logout', {'reason': 'sesiones_revocadas'}, to=f'user:{user_id}')
    except Exception as e:
        _logger.warning('force_logout_user emit falló user_id=%s err=%s', user_id, e)
    try:
        manager = socketio.server.manager
        ns_rooms = manager.rooms.get('/', {}) if hasattr(manager, 'rooms') else {}
        sids = list((ns_rooms.get(f'user:{user_id}') or {}).keys())
        for sid in sids:
            try:
                socketio.server.disconnect(sid, namespace='/')
            except Exception:
                pass
    except Exception as e:
        _logger.warning('force_logout_user disconnect local falló user_id=%s err=%s', user_id, e)


def emit_to_user(user_id: int, event: str, payload: dict) -> None:
    try:
        socketio.emit(event, payload, to=f'user:{user_id}')
    except Exception as e:
        _logger.warning('socket.emit_to_user falló user_id=%s event=%s err=%s', user_id, event, e)


def emit_to_role(roles, event: str, payload: dict) -> None:
    if isinstance(roles, str):
        roles = [roles]
    for r in roles or ():
        room = f'role:{(r or "").lower()}'
        if room == 'role:':
            continue
        try:
            socketio.emit(event, payload, to=room)
        except Exception as e:
            _logger.warning('socket.emit_to_role falló role=%s event=%s err=%s', r, event, e)


def emit_to_equipo(equipo_id: int, event: str, payload: dict) -> None:
    try:
        socketio.emit(event, payload, to=f'device:{equipo_id}', namespace='/agent')
    except Exception as e:
        _logger.warning('socket.emit_to_equipo falló equipo_id=%s event=%s err=%s', equipo_id, event, e)
