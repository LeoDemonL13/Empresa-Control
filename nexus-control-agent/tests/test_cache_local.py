import json
from datetime import date, timedelta

from agent import cache_local


def test_cargar_sin_archivo_devuelve_estado_vacio(tmp_path, monkeypatch):
    monkeypatch.setattr(cache_local, '_RUTA', str(tmp_path / 'estado.json'))
    estado = cache_local.cargar()
    assert estado['politica_version'] == 0
    assert estado['politicas'] == {}
    assert estado['acumulado'] == {}
    assert estado['fecha'] == date.today().isoformat()


def test_guardar_y_cargar(tmp_path, monkeypatch):
    ruta = tmp_path / 'subcarpeta' / 'estado.json'
    monkeypatch.setattr(cache_local, '_RUTA', str(ruta))

    estado = cache_local.cargar()
    estado['politica_version'] = 3
    estado['acumulado']['juego.exe'] = 120
    cache_local.guardar(estado)

    recargado = cache_local.cargar()
    assert recargado['politica_version'] == 3
    assert recargado['acumulado']['juego.exe'] == 120


def test_cargar_archivo_corrupto_devuelve_estado_vacio(tmp_path, monkeypatch):
    ruta = tmp_path / 'estado.json'
    ruta.write_text('esto no es json')
    monkeypatch.setattr(cache_local, '_RUTA', str(ruta))
    estado = cache_local.cargar()
    assert estado['acumulado'] == {}


def test_cambio_de_dia_reinicia_el_acumulado(tmp_path, monkeypatch):
    ruta = tmp_path / 'estado.json'
    ayer = (date.today() - timedelta(days=1)).isoformat()
    ruta.write_text(json.dumps({
        'politica_version': 2, 'politicas': {'juego.exe': {'estado': 'bloqueada'}},
        'fecha': ayer, 'acumulado': {'juego.exe': 500}, 'sesiones': {'juego.exe': 3}, 'activos': ['juego.exe'],
    }))
    monkeypatch.setattr(cache_local, '_RUTA', str(ruta))

    estado = cache_local.cargar()
    assert estado['fecha'] == date.today().isoformat()
    assert estado['acumulado'] == {}
    assert estado['sesiones'] == {}
    assert estado['politica_version'] == 2
    assert estado['politicas'] == {'juego.exe': {'estado': 'bloqueada'}}


def test_cargar_rellena_claves_faltantes_de_versiones_anteriores(tmp_path, monkeypatch):
    ruta = tmp_path / 'estado.json'
    ruta.write_text(json.dumps({'fecha': date.today().isoformat()}))
    monkeypatch.setattr(cache_local, '_RUTA', str(ruta))
    estado = cache_local.cargar()
    assert estado['politicas'] == {}
    assert estado['activos'] == []
