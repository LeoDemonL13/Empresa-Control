import logging
import os
import sys
from logging.handlers import RotatingFileHandler

from . import config


class _Flujo:
    def __init__(self, registro, nivel):
        self._registro = registro
        self._nivel = nivel

    def write(self, texto):
        for linea in str(texto).splitlines():
            if linea.strip():
                self._registro.log(self._nivel, linea)
        return len(texto)

    def flush(self):
        return None

    def isatty(self):
        return False


def redirigir_salida(ruta=None):
    ruta = ruta or config.ARCHIVO_LOG
    carpeta = os.path.dirname(ruta)
    if carpeta:
        os.makedirs(carpeta, exist_ok=True)
    registro = logging.getLogger('nexus-agente')
    registro.setLevel(logging.INFO)
    registro.propagate = False
    for manejador in list(registro.handlers):
        registro.removeHandler(manejador)
    manejador = RotatingFileHandler(ruta, maxBytes=1_000_000, backupCount=3, encoding='utf-8')
    manejador.setFormatter(logging.Formatter('%(asctime)s %(levelname)s %(message)s'))
    registro.addHandler(manejador)
    sys.stdout = _Flujo(registro, logging.INFO)
    sys.stderr = _Flujo(registro, logging.ERROR)
    return registro
