import json

from agent import almacen, config


def test_guardar_y_cargar(tmp_path, monkeypatch):
    ruta = tmp_path / 'subcarpeta' / 'device.json'
    monkeypatch.setattr(config, 'ARCHIVO_CREDENCIALES', str(ruta))

    almacen.guardar(7, 'clave-secreta', 'http://localhost:5001')
    cargado = almacen.cargar()

    assert cargado == {'equipo_id': 7, 'api_key': 'clave-secreta', 'api_base_url': 'http://localhost:5001'}


def test_cargar_sin_archivo_devuelve_none(tmp_path, monkeypatch):
    monkeypatch.setattr(config, 'ARCHIVO_CREDENCIALES', str(tmp_path / 'no-existe.json'))
    assert almacen.cargar() is None


def test_cargar_archivo_corrupto_devuelve_none(tmp_path, monkeypatch):
    ruta = tmp_path / 'device.json'
    ruta.write_text('esto no es json')
    monkeypatch.setattr(config, 'ARCHIVO_CREDENCIALES', str(ruta))
    assert almacen.cargar() is None


def test_cargar_archivo_incompleto_devuelve_none(tmp_path, monkeypatch):
    ruta = tmp_path / 'device.json'
    ruta.write_text(json.dumps({'equipo_id': 1}))
    monkeypatch.setattr(config, 'ARCHIVO_CREDENCIALES', str(ruta))
    assert almacen.cargar() is None


def test_borrar_elimina_el_archivo(tmp_path, monkeypatch):
    ruta = tmp_path / 'device.json'
    monkeypatch.setattr(config, 'ARCHIVO_CREDENCIALES', str(ruta))
    almacen.guardar(1, 'x', 'http://localhost:5001')
    assert ruta.exists()
    almacen.borrar()
    assert not ruta.exists()


def test_borrar_sin_archivo_no_falla(tmp_path, monkeypatch):
    monkeypatch.setattr(config, 'ARCHIVO_CREDENCIALES', str(tmp_path / 'no-existe.json'))
    almacen.borrar()
