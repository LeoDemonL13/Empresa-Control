from unittest.mock import patch

from agent import almacen, config
from agent.enrolamiento import asegurar_credenciales


def test_usa_credenciales_existentes_sin_pedir_nada(tmp_path, monkeypatch):
    ruta = tmp_path / 'device.json'
    monkeypatch.setattr(config, 'ARCHIVO_CREDENCIALES', str(ruta))
    almacen.guardar(5, 'clave-guardada', 'http://10.0.0.5:5001')

    with patch('builtins.input', side_effect=AssertionError('no debería pedir nada')):
        equipo_id, api_key, url = asegurar_credenciales()

    assert (equipo_id, api_key, url) == (5, 'clave-guardada', 'http://10.0.0.5:5001')


def test_enrola_y_guarda_cuando_no_hay_credenciales(tmp_path, monkeypatch):
    ruta = tmp_path / 'device.json'
    monkeypatch.setattr(config, 'ARCHIVO_CREDENCIALES', str(ruta))

    entradas = iter(['http://192.168.1.10:5001', 'ABCDE-FGHIJ'])
    with patch('builtins.input', lambda _: next(entradas)):
        with patch(
            'agent.enrolamiento.ClienteAPI.enrolar',
            return_value={'equipo_id': 3, 'api_key': 'nueva-clave', 'nombre': 'PC-Test'},
        ):
            equipo_id, api_key, url = asegurar_credenciales()

    assert (equipo_id, api_key, url) == (3, 'nueva-clave', 'http://192.168.1.10:5001')
    assert almacen.cargar() == {'equipo_id': 3, 'api_key': 'nueva-clave', 'api_base_url': 'http://192.168.1.10:5001'}


def test_usa_url_por_defecto_si_no_escriben_nada(tmp_path, monkeypatch):
    ruta = tmp_path / 'device.json'
    monkeypatch.setattr(config, 'ARCHIVO_CREDENCIALES', str(ruta))

    entradas = iter(['', 'ABCDE-FGHIJ'])
    with patch('builtins.input', lambda _: next(entradas)):
        with patch(
            'agent.enrolamiento.ClienteAPI.enrolar',
            return_value={'equipo_id': 1, 'api_key': 'k', 'nombre': 'PC'},
        ):
            _, _, url = asegurar_credenciales()

    assert url == config.URL_POR_DEFECTO
