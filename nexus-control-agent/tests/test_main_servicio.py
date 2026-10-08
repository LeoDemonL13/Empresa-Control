import sys

import pytest

import main
from agent import almacen, config, registro
from agent.cliente_api import ErrorAPI
from agent.enrolamiento import SinCredenciales, asegurar_credenciales, enrolar


def test_latir_seguro_devuelve_true_si_envia():
    assert main.latir_seguro(lambda: None) is True


def test_latir_seguro_no_propaga_errores_de_conexion(capsys):
    def falla():
        raise RuntimeError('sin conexion')

    assert main.latir_seguro(falla) is False
    assert 'sin conexion' in capsys.readouterr().out


def test_asegurar_credenciales_no_interactivo_sin_datos_falla_sin_preguntar(tmp_path, monkeypatch):
    monkeypatch.setattr(config, 'ARCHIVO_CREDENCIALES', str(tmp_path / 'device.json'))
    monkeypatch.setattr('builtins.input', lambda _: (_ for _ in ()).throw(AssertionError('no debe preguntar')))
    with pytest.raises(SinCredenciales):
        asegurar_credenciales(interactivo=False)


def test_enrolar_guarda_credenciales(tmp_path, monkeypatch):
    monkeypatch.setattr(config, 'ARCHIVO_CREDENCIALES', str(tmp_path / 'device.json'))
    monkeypatch.setattr(
        'agent.enrolamiento.ClienteAPI.enrolar',
        lambda self, codigo: {'equipo_id': 9, 'api_key': 'k', 'nombre': 'PC-9'},
    )
    resultado = enrolar(' https://nexus.ejemplo.com/ ', ' ABC ')
    assert resultado == (9, 'k', 'https://nexus.ejemplo.com', 'PC-9')
    assert almacen.cargar()['api_base_url'] == 'https://nexus.ejemplo.com'


def test_main_enrolar_con_argumentos_termina_sin_conectar(tmp_path, monkeypatch):
    monkeypatch.setattr(config, 'ARCHIVO_CREDENCIALES', str(tmp_path / 'device.json'))
    monkeypatch.setattr(config, 'ARCHIVO_LOG', str(tmp_path / 'agente.log'))
    monkeypatch.setattr(
        'agent.enrolamiento.ClienteAPI.enrolar',
        lambda self, codigo: {'equipo_id': 4, 'api_key': 'k4', 'nombre': 'PC-4'},
    )
    salida, error = sys.stdout, sys.stderr
    try:
        main.main(['--enrolar', 'http://10.0.0.2:5001', 'CODIGO'])
    finally:
        sys.stdout, sys.stderr = salida, error
    assert almacen.cargar()['equipo_id'] == 4
    assert 'Enrolado como' in (tmp_path / 'agente.log').read_text(encoding='utf-8')


def test_main_enrolar_con_codigo_invalido_sale_con_error(tmp_path, monkeypatch):
    monkeypatch.setattr(config, 'ARCHIVO_CREDENCIALES', str(tmp_path / 'device.json'))
    monkeypatch.setattr(config, 'ARCHIVO_LOG', str(tmp_path / 'agente.log'))

    def rechaza(self, codigo):
        raise ErrorAPI('Código inválido')

    monkeypatch.setattr('agent.enrolamiento.ClienteAPI.enrolar', rechaza)
    salida, error = sys.stdout, sys.stderr
    try:
        with pytest.raises(SystemExit) as info:
            main.main(['--enrolar', 'http://10.0.0.2:5001', 'MALO'])
    finally:
        sys.stdout, sys.stderr = salida, error
    assert info.value.code == 1
    assert almacen.cargar() is None


def test_main_servicio_sin_credenciales_sale_con_codigo_2(tmp_path, monkeypatch):
    monkeypatch.setattr(config, 'ARCHIVO_CREDENCIALES', str(tmp_path / 'device.json'))
    monkeypatch.setattr(config, 'ARCHIVO_LOG', str(tmp_path / 'agente.log'))
    salida, error = sys.stdout, sys.stderr
    try:
        with pytest.raises(SystemExit) as info:
            main.main(['--servicio'])
    finally:
        sys.stdout, sys.stderr = salida, error
    assert info.value.code == 2


def test_registro_escribe_en_archivo_y_rota(tmp_path):
    ruta = tmp_path / 'sub' / 'agente.log'
    salida, error = sys.stdout, sys.stderr
    try:
        registro.redirigir_salida(str(ruta))
        print('hola desde el agente')
        sys.stdout.flush()
    finally:
        sys.stdout, sys.stderr = salida, error
    assert 'hola desde el agente' in ruta.read_text(encoding='utf-8')
