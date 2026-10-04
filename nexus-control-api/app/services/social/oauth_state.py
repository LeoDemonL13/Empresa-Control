import base64
import hashlib
import secrets
from datetime import timedelta

from app.extensions import db
from app.models import SocialOAuthState, _now_utc
from app.services.social.fechas import asegurar_utc

DURACION_ESTADO_MINUTOS = 10


def generar_pkce():
    verifier = base64.urlsafe_b64encode(secrets.token_bytes(64)).rstrip(b'=').decode()
    digest = hashlib.sha256(verifier.encode()).digest()
    challenge = base64.urlsafe_b64encode(digest).rstrip(b'=').decode()
    return verifier, challenge


def crear_estado(plataforma, usuario_id, redirect_uri, code_verifier=None):
    valor = secrets.token_urlsafe(32)
    ahora = _now_utc()
    fila = SocialOAuthState(
        estado=valor,
        plataforma=plataforma,
        usuario_id=usuario_id,
        code_verifier=code_verifier,
        redirect_uri=redirect_uri,
        created_at=ahora,
        expira_at=ahora + timedelta(minutes=DURACION_ESTADO_MINUTOS),
    )
    db.session.add(fila)
    db.session.commit()
    return valor


def consumir_estado(valor, plataforma):
    if not valor:
        return None
    fila = SocialOAuthState.query.filter_by(estado=valor).first()
    if not fila:
        return None
    db.session.delete(fila)
    db.session.commit()
    if fila.plataforma != plataforma:
        return None
    if asegurar_utc(fila.expira_at) <= _now_utc():
        return None
    return fila


def limpiar_estados_expirados():
    SocialOAuthState.query.filter(SocialOAuthState.expira_at <= _now_utc()).delete(synchronize_session=False)
    db.session.commit()
