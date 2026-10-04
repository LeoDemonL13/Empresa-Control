from datetime import timedelta

from app.extensions import db
from app.models import SocialConnection, _now_utc
from app.realtime import _ejecutar_ciclo_sincronizacion_redes


def _conexion(plataforma='facebook', **extra):
    conexion = SocialConnection(plataforma=plataforma, estado='CONNECTED')
    conexion.access_token_cifrado = 'token-valido'
    conexion.expira_at = _now_utc() + timedelta(hours=2)
    for campo, valor in extra.items():
        setattr(conexion, campo, valor)
    db.session.add(conexion)
    db.session.commit()
    return conexion


def test_ciclo_sincroniza_conexion_sin_programacion_previa(app, monkeypatch):
    llamadas = []
    monkeypatch.setattr(
        'app.services.social.orchestrator.sincronizar_conexion',
        lambda conexion, disparado_por='programado', usuario=None: llamadas.append(conexion.plataforma),
    )
    _conexion('facebook')
    _ejecutar_ciclo_sincronizacion_redes()
    assert llamadas == ['facebook']


def test_ciclo_omite_conexion_bloqueada(app, monkeypatch):
    llamadas = []
    monkeypatch.setattr(
        'app.services.social.orchestrator.sincronizar_conexion',
        lambda conexion, disparado_por='programado', usuario=None: llamadas.append(conexion.plataforma),
    )
    _conexion('facebook', bloqueado_hasta=_now_utc() + timedelta(seconds=120))
    _ejecutar_ciclo_sincronizacion_redes()
    assert llamadas == []


def test_ciclo_omite_conexion_cuyo_proximo_ciclo_no_ha_llegado(app, monkeypatch):
    llamadas = []
    monkeypatch.setattr(
        'app.services.social.orchestrator.sincronizar_conexion',
        lambda conexion, disparado_por='programado', usuario=None: llamadas.append(conexion.plataforma),
    )
    _conexion('facebook', proxima_sincronizacion_at=_now_utc() + timedelta(minutes=10))
    _ejecutar_ciclo_sincronizacion_redes()
    assert llamadas == []


def test_ciclo_respeta_reintento_con_backoff_vencido(app, monkeypatch):
    llamadas = []
    monkeypatch.setattr(
        'app.services.social.orchestrator.sincronizar_conexion',
        lambda conexion, disparado_por='programado', usuario=None: llamadas.append(conexion.plataforma),
    )
    _conexion(
        'tiktok',
        proximo_reintento_at=_now_utc() - timedelta(seconds=1),
        proxima_sincronizacion_at=_now_utc() + timedelta(minutes=10),
    )
    _ejecutar_ciclo_sincronizacion_redes()
    assert llamadas == ['tiktok']


def test_ciclo_ignora_conexion_desconectada(app, monkeypatch):
    llamadas = []
    monkeypatch.setattr(
        'app.services.social.orchestrator.sincronizar_conexion',
        lambda conexion, disparado_por='programado', usuario=None: llamadas.append(conexion.plataforma),
    )
    conexion = _conexion('youtube')
    conexion.estado = 'DISCONNECTED'
    db.session.commit()
    _ejecutar_ciclo_sincronizacion_redes()
    assert llamadas == []


def test_ciclo_libera_el_bloqueo_tras_sincronizar(app, monkeypatch):
    monkeypatch.setattr(
        'app.services.social.orchestrator.sincronizar_conexion',
        lambda conexion, disparado_por='programado', usuario=None: None,
    )
    conexion = _conexion('facebook')
    _ejecutar_ciclo_sincronizacion_redes()
    db.session.refresh(conexion)
    assert conexion.bloqueado_hasta is None


def test_ciclo_libera_el_bloqueo_incluso_si_la_sincronizacion_lanza(app, monkeypatch):
    def _falla(conexion, disparado_por='programado', usuario=None):
        raise RuntimeError('boom')

    monkeypatch.setattr('app.services.social.orchestrator.sincronizar_conexion', _falla)
    conexion = _conexion('facebook')
    _ejecutar_ciclo_sincronizacion_redes()
    db.session.refresh(conexion)
    assert conexion.bloqueado_hasta is None
