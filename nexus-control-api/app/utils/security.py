import re

PASSWORD_MIN_LEN = 12

_PASSWORDS_PROHIBIDAS = {
    'password1!', 'password123!', 'passw0rd123!', 'contraseña1!',
    'contrasena1!', 'contrasena123!', 'qwerty123!', 'qwerty12345!',
    'admin1234!', 'administrador1!', 'bienvenido1!', 'bienvenido123!',
    'abcd1234!', 'abc12345!', 'usuario123!', 'sistema123!',
    'nexus123!', 'nexus1234!', 'p@ssw0rd', 'p@ssw0rd123',
}


def is_strong_password(password):
    if password is None:
        return False
    if len(password) < PASSWORD_MIN_LEN:
        return False
    if not re.search(r"[A-Z]", password):
        return False
    if not re.search(r"[a-z]", password):
        return False
    if not re.search(r"[0-9]", password):
        return False
    if not re.search(r"[^A-Za-z0-9]", password):
        return False
    if password.strip().lower() in _PASSWORDS_PROHIBIDAS:
        return False
    return True


def _safe_log_value(value, max_len: int = 200) -> str:
    s = str(value)
    s = s.replace('\r', '\\r').replace('\n', '\\n').replace('\t', '\\t')
    s = ''.join(ch if (ch >= ' ' or ch in ('\\',)) else '?' for ch in s)
    return s[:max_len]
