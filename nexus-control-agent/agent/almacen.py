import json
import os
import stat

from . import config


def guardar(equipo_id: int, api_key: str, api_base_url: str) -> None:
    carpeta = os.path.dirname(config.ARCHIVO_CREDENCIALES)
    if carpeta:
        os.makedirs(carpeta, exist_ok=True)
    with open(config.ARCHIVO_CREDENCIALES, 'w', encoding='utf-8') as f:
        json.dump({'equipo_id': equipo_id, 'api_key': api_key, 'api_base_url': api_base_url}, f)
    try:
        os.chmod(config.ARCHIVO_CREDENCIALES, stat.S_IRUSR | stat.S_IWUSR)
    except OSError:
        pass


def cargar() -> dict | None:
    if not os.path.exists(config.ARCHIVO_CREDENCIALES):
        return None
    try:
        with open(config.ARCHIVO_CREDENCIALES, 'r', encoding='utf-8') as f:
            datos = json.load(f)
    except (OSError, ValueError):
        return None
    if not all(k in datos for k in ('equipo_id', 'api_key', 'api_base_url')):
        return None
    return datos


def borrar() -> None:
    try:
        os.remove(config.ARCHIVO_CREDENCIALES)
    except OSError:
        pass
