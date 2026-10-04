import platform
import socket
import uuid


def _mac_local() -> str | None:
    nodo = uuid.getnode()
    if (nodo >> 40) % 2 == 1:
        return None
    partes = [f'{(nodo >> despl) & 0xff:02X}' for despl in range(40, -8, -8)]
    return ':'.join(partes)


def _ip_local() -> str | None:
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('8.8.8.8', 80))
        return s.getsockname()[0]
    except OSError:
        return None
    finally:
        s.close()


def recolectar() -> dict:
    return {
        'hostname': socket.gethostname(),
        'ip': _ip_local(),
        'mac': _mac_local(),
        'sistema_operativo': f'{platform.system()} {platform.release()}'.strip(),
    }
