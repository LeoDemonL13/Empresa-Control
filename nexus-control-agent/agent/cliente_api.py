import requests

from . import config


class ErrorAPI(Exception):
    def __init__(self, mensaje: str, status_code: int | None = None):
        super().__init__(mensaje)
        self.status_code = status_code


class ClienteAPI:
    def __init__(self, api_base_url: str, equipo_id: int | None = None, api_key: str | None = None):
        self.api_base_url = api_base_url.rstrip('/')
        self.equipo_id = equipo_id
        self.api_key = api_key

    def _cabeceras(self) -> dict:
        return {'X-Device-Id': str(self.equipo_id), 'X-Api-Key': self.api_key}

    def _error_de(self, respuesta) -> str:
        try:
            return respuesta.json().get('error') or respuesta.text
        except ValueError:
            return respuesta.text or f'Error HTTP {respuesta.status_code}'

    def enrolar(self, codigo: str) -> dict:
        try:
            r = requests.post(f'{self.api_base_url}/api/agente/enrolar', json={'codigo': codigo}, timeout=10)
        except requests.RequestException as e:
            raise ErrorAPI(f'No se pudo contactar al servidor: {e}') from e
        if not r.ok:
            raise ErrorAPI(self._error_de(r), r.status_code)
        return r.json()

    def enviar_inventario(self, datos: dict) -> dict:
        payload = {**datos, 'agente_version': config.AGENTE_VERSION}
        try:
            r = requests.post(
                f'{self.api_base_url}/api/agente/inventario',
                json=payload,
                headers=self._cabeceras(),
                timeout=10,
            )
        except requests.RequestException as e:
            raise ErrorAPI(f'No se pudo contactar al servidor: {e}') from e
        if not r.ok:
            raise ErrorAPI(self._error_de(r), r.status_code)
        return r.json()

    def obtener_politicas(self) -> dict:
        try:
            r = requests.get(
                f'{self.api_base_url}/api/agente/politicas',
                headers=self._cabeceras(),
                timeout=10,
            )
        except requests.RequestException as e:
            raise ErrorAPI(f'No se pudo contactar al servidor: {e}') from e
        if not r.ok:
            raise ErrorAPI(self._error_de(r), r.status_code)
        return r.json()

    def enviar_uso(self, fecha: str, entradas: list) -> dict:
        try:
            r = requests.post(
                f'{self.api_base_url}/api/agente/uso',
                json={'fecha': fecha, 'entradas': entradas},
                headers=self._cabeceras(),
                timeout=10,
            )
        except requests.RequestException as e:
            raise ErrorAPI(f'No se pudo contactar al servidor: {e}') from e
        if not r.ok:
            raise ErrorAPI(self._error_de(r), r.status_code)
        return r.json()
