from app import realtime


def test_intervalo_usa_60_minutos_por_defecto(monkeypatch):
    monkeypatch.delenv('INTERVALO_SINCRONIZACION_REDES_MINUTOS', raising=False)
    assert realtime._intervalo_sincronizacion_segundos() == 60 * 60


def test_intervalo_respeta_la_variable_de_entorno(monkeypatch):
    monkeypatch.setenv('INTERVALO_SINCRONIZACION_REDES_MINUTOS', '15')
    assert realtime._intervalo_sincronizacion_segundos() == 15 * 60


def test_intervalo_tiene_un_minimo_de_seguridad(monkeypatch):
    monkeypatch.setenv('INTERVALO_SINCRONIZACION_REDES_MINUTOS', '1')
    assert realtime._intervalo_sincronizacion_segundos() == 5 * 60


def test_intervalo_con_valor_invalido_cae_al_valor_por_defecto(monkeypatch):
    monkeypatch.setenv('INTERVALO_SINCRONIZACION_REDES_MINUTOS', 'no-es-numero')
    assert realtime._intervalo_sincronizacion_segundos() == 60 * 60


def test_no_inicia_el_programador_mientras_la_app_esta_en_pruebas(app, monkeypatch):
    assert app.config.get('TESTING') is True
    monkeypatch.setattr(realtime, '_sincronizacion_redes_iniciada', False)
    realtime._iniciar_sincronizacion_redes_sociales(app)
    assert realtime._sincronizacion_redes_iniciada is False
