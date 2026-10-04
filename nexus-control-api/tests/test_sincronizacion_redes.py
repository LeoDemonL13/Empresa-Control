from app.extensions import db
from app.models import ConexionRedSocial, MetricaSocial
from app.services import sincronizacion_redes


def _crear_conexion(plataforma, credenciales=None):
    c = ConexionRedSocial(plataforma=plataforma, credenciales_cifradas=credenciales or {'token_acceso': 'x', 'id_pagina': '1'})
    db.session.add(c)
    db.session.commit()
    return c


def test_sincronizar_plataforma_sin_conexion_devuelve_error(app):
    with app.app_context():
        ok, error = sincronizacion_redes.sincronizar_plataforma('facebook')
        assert ok is False
        assert 'credenciales' in error


def test_sincronizar_plataforma_exitosa_actualiza_metrica_y_conexion(app, monkeypatch):
    with app.app_context():
        _crear_conexion('facebook')
        monkeypatch.setitem(
            sincronizacion_redes.CLIENTES_POR_PLATAFORMA, 'facebook',
            lambda creds: {'me_gusta': 500, 'interacciones': 40, 'impresiones': 2000, 'engagement': 2.0},
        )

        ok, error = sincronizacion_redes.sincronizar_plataforma('facebook')

        assert ok is True
        assert error is None

        metrica = MetricaSocial.query.filter_by(red_social_normalizada='facebook').one()
        assert metrica.me_gusta == 500
        assert metrica.origen == 'automatico'
        assert metrica.actualizado_por == sincronizacion_redes.ACTUALIZADO_POR_SINCRONIZACION

        conexion = ConexionRedSocial.query.filter_by(plataforma='facebook').one()
        assert conexion.ultimo_error is None
        assert conexion.ultima_sincronizacion is not None


def test_sincronizar_plataforma_con_fallo_guarda_ultimo_error(app, monkeypatch):
    with app.app_context():
        _crear_conexion('x', {'bearer_token': 'tok', 'nombre_usuario': 'empresa'})

        def _falla(creds):
            from app.services.redes_sociales import ErrorSincronizacion
            raise ErrorSincronizacion('la cuenta no existe')

        monkeypatch.setitem(sincronizacion_redes.CLIENTES_POR_PLATAFORMA, 'x', _falla)

        ok, error = sincronizacion_redes.sincronizar_plataforma('x')

        assert ok is False
        assert error == 'la cuenta no existe'

        conexion = ConexionRedSocial.query.filter_by(plataforma='x').one()
        assert conexion.ultimo_error == 'la cuenta no existe'
        assert conexion.ultima_sincronizacion is not None
        assert MetricaSocial.query.filter_by(red_social_normalizada='x').count() == 0


def test_sincronizar_todas_recorre_cada_conexion_guardada(app, monkeypatch):
    with app.app_context():
        _crear_conexion('facebook')
        _crear_conexion('youtube', {'clave_api': 'k', 'id_canal': 'c1'})

        monkeypatch.setitem(
            sincronizacion_redes.CLIENTES_POR_PLATAFORMA, 'facebook',
            lambda creds: {'me_gusta': 10, 'interacciones': 1, 'impresiones': 100, 'engagement': 1.0},
        )
        monkeypatch.setitem(
            sincronizacion_redes.CLIENTES_POR_PLATAFORMA, 'youtube',
            lambda creds: {'me_gusta': 20, 'interacciones': 2, 'impresiones': 200, 'engagement': 1.0},
        )

        resultados = sincronizacion_redes.sincronizar_todas()

        assert resultados['facebook']['ok'] is True
        assert resultados['youtube']['ok'] is True
        assert MetricaSocial.query.count() == 2


def test_sincronizar_plataforma_no_soportada(app):
    with app.app_context():
        _crear_conexion('mastodon', {'token_acceso': 'x'})
        ok, error = sincronizacion_redes.sincronizar_plataforma('mastodon')
        assert ok is False
        assert 'no soportada' in error
