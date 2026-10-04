import base64
import ipaddress
import json
import os

import redis
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from flask import request as flask_request
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect
from sqlalchemy import String, Text
from sqlalchemy.types import TypeDecorator


def _fernet_desde_env():
    key = os.environ.get('TOTP_ENCRYPTION_KEY', '').strip()
    if not key:
        raise RuntimeError(
            "CRÍTICO: TOTP_ENCRYPTION_KEY no configurada. "
            "Genera una clave con: python -c \"from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())\""
        )
    return Fernet(key.encode() if isinstance(key, str) else key)


class EncryptedString(TypeDecorator):
    impl = String(500)
    cache_ok = True

    def _fernet(self):
        return _fernet_desde_env()

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        return self._fernet().encrypt(value.encode()).decode()

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        try:
            return self._fernet().decrypt(value.encode()).decode()
        except Exception:
            return value


class EncryptedJSON(TypeDecorator):
    impl = Text
    cache_ok = True

    def _fernet(self):
        return _fernet_desde_env()

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        crudo = json.dumps(value, ensure_ascii=False, separators=(',', ':'))
        return self._fernet().encrypt(crudo.encode()).decode()

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        try:
            crudo = self._fernet().decrypt(value.encode()).decode()
            return json.loads(crudo)
        except Exception:
            return None


def _aesgcm_desde_env():
    key_b64 = os.environ.get('SOCIAL_TOKEN_ENCRYPTION_KEY', '').strip()
    if not key_b64:
        raise RuntimeError(
            "CRÍTICO: SOCIAL_TOKEN_ENCRYPTION_KEY no configurada. "
            "Genera una clave con: python -c \"import base64, os; "
            "print(base64.urlsafe_b64encode(os.urandom(32)).decode())\""
        )
    try:
        key = base64.urlsafe_b64decode(key_b64.encode())
    except Exception as exc:
        raise RuntimeError(
            "CRÍTICO: SOCIAL_TOKEN_ENCRYPTION_KEY no es base64 urlsafe válido."
        ) from exc
    if len(key) != 32:
        raise RuntimeError(
            "CRÍTICO: SOCIAL_TOKEN_ENCRYPTION_KEY debe decodificar a 32 bytes "
            "(AES-256-GCM)."
        )
    return AESGCM(key)


class SocialEncryptedString(TypeDecorator):
    """Cadena cifrada con AES-256-GCM (autenticado), para tokens OAuth.

    Independiente de EncryptedString/EncryptedJSON (Fernet, usados para TOTP):
    usa su propia clave maestra (SOCIAL_TOKEN_ENCRYPTION_KEY) para que la
    rotación o el compromiso de una clave no afecte a la otra.
    """

    impl = Text
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        aes = _aesgcm_desde_env()
        nonce = os.urandom(12)
        cifrado = aes.encrypt(nonce, value.encode(), None)
        return base64.urlsafe_b64encode(nonce + cifrado).decode()

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        try:
            crudo = base64.urlsafe_b64decode(value.encode())
            nonce, cifrado = crudo[:12], crudo[12:]
            aes = _aesgcm_desde_env()
            return aes.decrypt(nonce, cifrado, None).decode()
        except Exception:
            return None


db = SQLAlchemy()
csrf = CSRFProtect()
migrate = Migrate()

_CF_CIDRS = [
    "103.21.244.0/22", "103.22.200.0/22", "103.31.4.0/22",
    "104.16.0.0/13", "104.24.0.0/14", "108.162.192.0/18",
    "131.0.72.0/22", "141.101.64.0/18", "162.158.0.0/15",
    "172.64.0.0/13", "173.245.48.0/20", "188.114.96.0/20",
    "190.93.240.0/20", "197.234.240.0/22", "198.41.128.0/17",
]
_CF_NETWORKS = [ipaddress.ip_network(cidr, strict=False) for cidr in _CF_CIDRS]


def is_cloudflare_ip(ip: str) -> bool:
    try:
        addr = ipaddress.ip_address(ip)
        return any(addr in net for net in _CF_NETWORKS)
    except ValueError:
        return False


_redis_client = None


def get_redis():
    global _redis_client
    if _redis_client is None:
        redis_url = os.environ.get('REDIS_URL')
        if redis_url and not redis_url.startswith('memory://'):
            try:
                _redis_client = redis.from_url(
                    redis_url,
                    decode_responses=True,
                    socket_connect_timeout=2,
                    socket_timeout=2,
                    health_check_interval=30,
                    retry_on_timeout=False,
                )
                _redis_client.ping()
            except Exception:
                _redis_client = None
    return _redis_client


def redis_call(operacion, default=None):
    global _redis_client
    r = get_redis()
    if r is None:
        return default
    try:
        return operacion(r)
    except Exception:
        _redis_client = None
        try:
            import logging
            logging.getLogger(__name__).warning(
                'Redis no respondió; degradando esta operación al default (%r). '
                'Mientras dure, se pierden: blacklist de jti, lockout escalado, '
                'anti-replay de TOTP y consumo del stepToken.', default,
            )
        except Exception:
            pass
        return default


def get_real_client_ip_flask() -> str:
    remote = flask_request.remote_addr or ""
    cf_ip = flask_request.headers.get("CF-Connecting-IP")
    if cf_ip and is_cloudflare_ip(remote):
        return cf_ip.strip()
    return get_remote_address()


def rate_limit_key() -> str:
    return get_real_client_ip_flask()


limiter = Limiter(key_func=rate_limit_key)
