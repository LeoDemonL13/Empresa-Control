from unittest.mock import Mock

from agent import cache_local, politicas


def test_refrescar_politicas_guarda_el_mapa_por_ejecutable(tmp_path, monkeypatch):
    monkeypatch.setattr(cache_local, '_RUTA', str(tmp_path / 'estado.json'))
    cliente = Mock()
    cliente.obtener_politicas.return_value = {
        'politica_version': 4,
        'politicas': [
            {'ejecutable': 'juego.exe', 'estado': 'bloqueada', 'tipo_uso': 'sin_limite', 'limite_minutos': None},
        ],
    }

    estado = politicas.refrescar_politicas(cliente)
    assert estado['politica_version'] == 4
    assert estado['politicas']['juego.exe']['estado'] == 'bloqueada'


def test_enviar_uso_acumulado_sin_datos_no_llama_al_cliente(tmp_path, monkeypatch):
    monkeypatch.setattr(cache_local, '_RUTA', str(tmp_path / 'estado.json'))
    cliente = Mock()
    resultado = politicas.enviar_uso_acumulado(cliente)
    assert resultado is False
    cliente.enviar_uso.assert_not_called()


def test_enviar_uso_acumulado_envia_las_entradas_acumuladas(tmp_path, monkeypatch):
    monkeypatch.setattr(cache_local, '_RUTA', str(tmp_path / 'estado.json'))
    estado = cache_local.cargar()
    estado['acumulado'] = {'notas.exe': 90}
    estado['sesiones'] = {'notas.exe': 2}
    cache_local.guardar(estado)

    cliente = Mock()
    resultado = politicas.enviar_uso_acumulado(cliente)

    assert resultado is True
    args, _ = cliente.enviar_uso.call_args
    assert args[0] == estado['fecha']
    assert args[1] == [{'ejecutable': 'notas.exe', 'segundos': 90, 'sesiones': 2}]


def test_enviar_uso_acumulado_solo_envia_lo_nuevo_desde_el_ultimo_envio(tmp_path, monkeypatch):
    monkeypatch.setattr(cache_local, '_RUTA', str(tmp_path / 'estado.json'))
    estado = cache_local.cargar()
    estado['acumulado'] = {'notas.exe': 90}
    estado['sesiones'] = {'notas.exe': 2}
    cache_local.guardar(estado)

    cliente = Mock()
    politicas.enviar_uso_acumulado(cliente)

    estado_tras_primer_envio = cache_local.cargar()
    estado_tras_primer_envio['acumulado']['notas.exe'] += 30
    estado_tras_primer_envio['sesiones']['notas.exe'] = 1
    cache_local.guardar(estado_tras_primer_envio)

    resultado = politicas.enviar_uso_acumulado(cliente)

    assert resultado is True
    args, _ = cliente.enviar_uso.call_args
    assert args[1] == [{'ejecutable': 'notas.exe', 'segundos': 30, 'sesiones': 1}]


def test_enviar_uso_acumulado_no_reenvia_lo_ya_confirmado(tmp_path, monkeypatch):
    monkeypatch.setattr(cache_local, '_RUTA', str(tmp_path / 'estado.json'))
    estado = cache_local.cargar()
    estado['acumulado'] = {'notas.exe': 90}
    estado['sesiones'] = {'notas.exe': 2}
    cache_local.guardar(estado)

    cliente = Mock()
    politicas.enviar_uso_acumulado(cliente)
    cliente.enviar_uso.reset_mock()

    resultado = politicas.enviar_uso_acumulado(cliente)

    assert resultado is False
    cliente.enviar_uso.assert_not_called()
