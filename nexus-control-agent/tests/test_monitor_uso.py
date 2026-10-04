from unittest.mock import patch

from agent import cache_local, monitor_uso


def _estado_base(**overrides):
    estado = cache_local._vacio()
    estado.update(overrides)
    return estado


def test_escanear_procesos_agrupa_por_nombre():
    class _Proceso:
        def __init__(self, pid, name):
            self.info = {'pid': pid, 'name': name}

    with patch('agent.monitor_uso.psutil.process_iter', return_value=[
        _Proceso(10, 'chrome.exe'), _Proceso(11, 'chrome.exe'), _Proceso(12, 'juego.exe'),
    ]):
        procesos = monitor_uso.escanear_procesos()
    assert sorted(procesos['chrome.exe']) == [10, 11]
    assert procesos['juego.exe'] == [12]


def test_debe_bloquear_sin_politica_es_false():
    assert monitor_uso._debe_bloquear(None, 0) is False


def test_debe_bloquear_aplicacion_bloqueada():
    assert monitor_uso._debe_bloquear({'estado': 'bloqueada', 'tipo_uso': 'sin_limite'}, 0) is True


def test_debe_bloquear_con_limite_no_alcanzado():
    politica = {'estado': 'permitida', 'tipo_uso': 'con_limite', 'limite_minutos': 10}
    assert monitor_uso._debe_bloquear(politica, 100) is False


def test_debe_bloquear_con_limite_alcanzado():
    politica = {'estado': 'permitida', 'tipo_uso': 'con_limite', 'limite_minutos': 1}
    assert monitor_uso._debe_bloquear(politica, 65) is True


def test_aplicar_ciclo_acumula_tiempo_de_procesos_permitidos(tmp_path, monkeypatch):
    monkeypatch.setattr(cache_local, '_RUTA', str(tmp_path / 'estado.json'))
    cache_local.guardar(_estado_base(politicas={'notas.exe': {'estado': 'permitida', 'tipo_uso': 'sin_limite'}}))

    estado = monitor_uso.aplicar_ciclo(15, procesos={'notas.exe': [100]})
    assert estado['acumulado']['notas.exe'] == 15
    assert estado['sesiones']['notas.exe'] == 1


def test_aplicar_ciclo_termina_proceso_con_limite_alcanzado(tmp_path, monkeypatch):
    monkeypatch.setattr(cache_local, '_RUTA', str(tmp_path / 'estado.json'))
    cache_local.guardar(_estado_base(
        politicas={'juego.exe': {'estado': 'permitida', 'tipo_uso': 'con_limite', 'limite_minutos': 1}},
        acumulado={'juego.exe': 65},
        activos=['juego.exe'],
    ))

    with patch('agent.monitor_uso.enforcement.terminar_proceso') as mock_terminar:
        estado = monitor_uso.aplicar_ciclo(15, procesos={'juego.exe': [200]})

    mock_terminar.assert_called_once_with(200)
    assert estado['acumulado']['juego.exe'] == 65


def test_aplicar_ciclo_bloquea_aplicacion_marcada_bloqueada(tmp_path, monkeypatch):
    monkeypatch.setattr(cache_local, '_RUTA', str(tmp_path / 'estado.json'))
    cache_local.guardar(_estado_base(politicas={'juego.exe': {'estado': 'bloqueada', 'tipo_uso': 'sin_limite'}}))

    with patch('agent.monitor_uso.enforcement.terminar_proceso') as mock_terminar:
        monitor_uso.aplicar_ciclo(15, procesos={'juego.exe': [300, 301]})

    assert mock_terminar.call_count == 2
