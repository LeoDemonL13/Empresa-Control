from datetime import datetime, timezone


def asegurar_utc(valor):
    if valor is None:
        return None
    if valor.tzinfo is None:
        return valor.replace(tzinfo=timezone.utc)
    return valor


def parsear_fecha(valor):
    if valor is None or valor == '':
        return None
    if isinstance(valor, (int, float)):
        return datetime.fromtimestamp(valor, tz=timezone.utc)
    texto = str(valor).strip()
    if texto.endswith('Z'):
        texto = texto[:-1] + '+0000'
    try:
        return datetime.strptime(texto, '%Y-%m-%dT%H:%M:%S%z')
    except ValueError:
        pass
    try:
        return datetime.fromisoformat(texto)
    except ValueError:
        return None
