from datetime import timedelta

import pytest

from app.extensions import db
from app.models import (
    ESTADO_CONECTADO,
    ESTADO_ERROR,
    ESTADO_REAUTH_REQUERIDA,
    SocialAccount,
    SocialConnection,
    SocialOAuthState,
    _now_utc,
)
from app.services.social import credential_manager, oauth_state, orchestrator
from app.services.social.errors import ReauthRequired, SocialProviderError
from app.services.social.fechas import asegurar_utc
from app.services.social.providers.base import SocialProvider


def test_social_encrypted_string_cifra_en_reposo(app):
    conexion = SocialConnection(plataforma='facebook')
    conexion.access_token_cifrado = 'token-secreto-de-prueba'
    db.session.add(conexion)
    db.session.commit()

    crudo = db.session.execute(
        db.text('SELECT access_token_cifrado FROM social_connections WHERE id = :id'),
        {'id': conexion.id},
    ).scalar()
    assert crudo != 'token-secreto-de-prueba'
    assert 'token-secreto-de-prueba' not in crudo

    db.session.expire_all()
    recargada = db.session.get(SocialConnection, conexion.id)
    assert recargada.access_token_cifrado == 'token-secreto-de-prueba'


def test_oauth_state_crear_y_consumir(app, super_admin):
    valor = oauth_state.crear_estado('tiktok', super_admin.id, 'http://localhost/callback', 'verifier-123')
    fila = oauth_state.consumir_estado(valor, 'tiktok')
    assert fila is not None
    assert fila.usuario_id == super_admin.id
    assert fila.code_verifier == 'verifier-123'

    assert SocialOAuthState.query.count() == 0
    assert oauth_state.consumir_estado(valor, 'tiktok') is None


def test_oauth_state_rechaza_plataforma_distinta(app, super_admin):
    valor = oauth_state.crear_estado('facebook', super_admin.id, 'http://localhost/callback')
    assert oauth_state.consumir_estado(valor, 'instagram') is None


def test_oauth_state_rechaza_expirado(app, super_admin):
    valor = oauth_state.crear_estado('youtube', super_admin.id, 'http://localhost/callback')
    fila = SocialOAuthState.query.filter_by(estado=valor).first()
    fila.expira_at = _now_utc() - timedelta(minutes=1)
    db.session.commit()
    assert oauth_state.consumir_estado(valor, 'youtube') is None


def test_generar_pkce_produce_challenge_derivado_del_verifier():
    import base64
    import hashlib

    verifier, challenge = oauth_state.generar_pkce()
    esperado = base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest()).rstrip(b'=').decode()
    assert challenge == esperado


def test_credential_manager_token_vigente_no_refresca(app):
    conexion = SocialConnection(plataforma='youtube', estado=ESTADO_CONECTADO)
    conexion.access_token_cifrado = 'token-valido'
    conexion.expira_at = _now_utc() + timedelta(hours=2)
    db.session.add(conexion)
    db.session.commit()

    token = credential_manager.obtener_token_vigente(conexion)
    assert token == 'token-valido'


def test_credential_manager_sin_token_requiere_reauth(app):
    conexion = SocialConnection(plataforma='youtube')
    db.session.add(conexion)
    db.session.commit()
    with pytest.raises(ReauthRequired):
        credential_manager.obtener_token_vigente(conexion)


def test_credential_manager_refresca_token_por_expirar(app, monkeypatch):
    conexion = SocialConnection(plataforma='youtube', estado=ESTADO_CONECTADO)
    conexion.access_token_cifrado = 'token-viejo'
    conexion.refresh_token_cifrado = 'refresh-valido'
    conexion.expira_at = _now_utc() + timedelta(seconds=30)
    db.session.add(conexion)
    db.session.commit()

    def refresh_falso(refresh_token):
        assert refresh_token == 'refresh-valido'
        return {'access_token': 'token-nuevo', 'expires_in': 3600, 'token_type': 'Bearer'}

    proveedor = credential_manager.proveedor_para('youtube')
    monkeypatch.setattr(proveedor, 'refresh_token', refresh_falso)

    token = credential_manager.obtener_token_vigente(conexion)
    assert token == 'token-nuevo'
    assert conexion.estado == ESTADO_CONECTADO
    assert conexion.errores_consecutivos == 0


def test_credential_manager_refresh_expirado_marca_reauth(app, monkeypatch):
    conexion = SocialConnection(plataforma='tiktok', estado=ESTADO_CONECTADO)
    conexion.access_token_cifrado = 'token-viejo'
    conexion.refresh_token_cifrado = 'refresh-vencido'
    conexion.expira_at = _now_utc() - timedelta(seconds=5)
    db.session.add(conexion)
    db.session.commit()

    def refresh_falla(refresh_token):
        raise SocialProviderError('refresh_expirado', 'TikTok rechazó el refresh token')

    proveedor = credential_manager.proveedor_para('tiktok')
    monkeypatch.setattr(proveedor, 'refresh_token', refresh_falla)

    with pytest.raises(ReauthRequired):
        credential_manager.obtener_token_vigente(conexion)
    assert conexion.estado == ESTADO_REAUTH_REQUERIDA


def test_credential_manager_backoff_escalona_reintentos(app):
    conexion = SocialConnection(plataforma='facebook', estado=ESTADO_CONECTADO)
    conexion.access_token_cifrado = 'x'
    db.session.add(conexion)
    db.session.commit()

    credential_manager.marcar_error(conexion, SocialProviderError('timeout', 'tardó demasiado'))
    primer_reintento = asegurar_utc(conexion.proximo_reintento_at)
    assert conexion.estado == ESTADO_ERROR
    assert primer_reintento > _now_utc()

    credential_manager.marcar_error(conexion, SocialProviderError('timeout', 'tardó demasiado'))
    segundo_reintento = asegurar_utc(conexion.proximo_reintento_at)
    assert segundo_reintento > primer_reintento


def test_credential_manager_respeta_retry_after(app):
    conexion = SocialConnection(plataforma='facebook', estado=ESTADO_CONECTADO)
    conexion.access_token_cifrado = 'x'
    db.session.add(conexion)
    db.session.commit()

    credential_manager.marcar_error(conexion, SocialProviderError('limite_tasa', 'demasiadas solicitudes', retry_after=600))
    assert asegurar_utc(conexion.proximo_reintento_at) >= _now_utc() + timedelta(minutes=9)


class _ProveedorFalso(SocialProvider):
    platform_id = 'facebook'
    usa_pkce = False

    def __init__(self):
        self.cuentas = [{'id_externo': 'pagina-1', 'nombre': 'Página de prueba', 'usuario': None, 'url_imagen': None, 'metadatos': {}}]
        self.perfil = {'seguidores': 1000}
        self.posts = [{
            'id_externo_post': 'post-1',
            'tipo': 'post',
            'permalink': 'https://facebook.com/post-1',
            'extracto': 'Hola mundo',
            'publicado_at': _now_utc().isoformat(),
            'metricas': {'me_gusta': 10, 'comentarios': 2, 'compartidos': 1, 'impresiones': 500, 'vistas': None},
        }]

    def build_authorize_url(self, state, redirect_uri, code_challenge=None):
        return 'https://example.com/oauth'

    def exchange_code(self, code, redirect_uri, code_verifier=None):
        return {'access_token': 'tok', 'expires_in': 3600}

    def refresh_token(self, refresh_token):
        return {'access_token': 'tok2', 'expires_in': 3600}

    def get_accounts(self, access_token):
        return self.cuentas

    def sync_profile(self, access_token, account):
        return self.perfil

    def sync_posts(self, access_token, account, limite=25):
        return self.posts

    def revoke(self, access_token, refresh_token=None):
        return True

    def check_connection(self, access_token):
        return True


def test_orchestrator_sincroniza_cuenta_y_posts(app, monkeypatch):
    proveedor_falso = _ProveedorFalso()
    monkeypatch.setattr('app.services.social.orchestrator.proveedor_para', lambda p: proveedor_falso)

    conexion = SocialConnection(plataforma='facebook', estado=ESTADO_CONECTADO)
    conexion.access_token_cifrado = 'token-valido'
    conexion.expira_at = _now_utc() + timedelta(hours=1)
    db.session.add(conexion)
    db.session.commit()

    run = orchestrator.sincronizar_conexion(conexion, disparado_por='manual', usuario='root@nexus.mx')

    assert run.estado == 'ok'
    assert conexion.ultima_sincronizacion_at is not None
    assert conexion.proxima_sincronizacion_at is not None

    cuenta = SocialAccount.query.filter_by(plataforma='facebook', id_externo='pagina-1').first()
    assert cuenta is not None
    assert cuenta.nombre == 'Página de prueba'
    assert len(cuenta.posts) == 1
    assert cuenta.posts[0].metricas.me_gusta == 10

    from app.models import MetricaSocial
    metrica = MetricaSocial.query.filter_by(red_social_normalizada='facebook').first()
    assert metrica is not None
    assert metrica.origen == 'automatico'
    assert metrica.me_gusta == 10


def test_orchestrator_marca_reauth_si_proveedor_lo_exige(app, monkeypatch):
    class _ProveedorReauth(_ProveedorFalso):
        def get_accounts(self, access_token):
            raise SocialProviderError('permisos_revocados', 'revocado')

    monkeypatch.setattr('app.services.social.orchestrator.proveedor_para', lambda p: _ProveedorReauth())

    conexion = SocialConnection(plataforma='facebook', estado=ESTADO_CONECTADO)
    conexion.access_token_cifrado = 'token'
    conexion.expira_at = _now_utc() + timedelta(hours=1)
    db.session.add(conexion)
    db.session.commit()

    run = orchestrator.sincronizar_conexion(conexion, disparado_por='programado')
    assert run.estado == 'error'
    assert conexion.estado == ESTADO_REAUTH_REQUERIDA
