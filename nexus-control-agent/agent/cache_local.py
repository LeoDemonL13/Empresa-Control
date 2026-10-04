import json
import os
from datetime import date

_RUTA = os.environ.get(
    'NEXUS_ESTADO_PATH',
    os.path.join(os.environ.get('PROGRAMDATA', '.'), 'NexusObsidianControl', 'estado.json'),
)


def _vacio() -> dict:
    return {
        'politica_version': 0,
        'politicas': {},
        'fecha': date.today().isoformat(),
        'acumulado': {},
        'sesiones': {},
        'activos': [],
    }


def cargar() -> dict:
    if not os.path.exists(_RUTA):
        return _vacio()
    try:
        with open(_RUTA, 'r', encoding='utf-8') as f:
            estado = json.load(f)
    except (OSError, ValueError):
        return _vacio()

    for clave, valor in _vacio().items():
        estado.setdefault(clave, valor)

    if estado.get('fecha') != date.today().isoformat():
        estado['fecha'] = date.today().isoformat()
        estado['acumulado'] = {}
        estado['sesiones'] = {}

    return estado


def guardar(estado: dict) -> None:
    carpeta = os.path.dirname(_RUTA)
    if carpeta:
        os.makedirs(carpeta, exist_ok=True)
    with open(_RUTA, 'w', encoding='utf-8') as f:
        json.dump(estado, f)
