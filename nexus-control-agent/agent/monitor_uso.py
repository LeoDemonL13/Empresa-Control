import psutil

from . import cache_local, enforcement


def escanear_procesos() -> dict:
    procesos = {}
    for proceso in psutil.process_iter(['pid', 'name']):
        nombre = (proceso.info.get('name') or '').lower()
        if not nombre:
            continue
        procesos.setdefault(nombre, []).append(proceso.info['pid'])
    return procesos


def _debe_bloquear(politica: dict | None, acumulado_segundos: int) -> bool:
    if not politica:
        return False
    if politica.get('estado') == 'bloqueada':
        return True
    if politica.get('tipo_uso') == 'con_limite':
        limite_segundos = (politica.get('limite_minutos') or 0) * 60
        if limite_segundos and acumulado_segundos >= limite_segundos:
            return True
    return False


def aplicar_ciclo(intervalo_segundos: int, procesos: dict | None = None) -> dict:
    estado = cache_local.cargar()
    if procesos is None:
        procesos = escanear_procesos()

    activos_previos = set(estado.get('activos') or [])
    activos_actuales = set(procesos.keys())
    for nuevo in activos_actuales - activos_previos:
        estado['sesiones'][nuevo] = estado['sesiones'].get(nuevo, 0) + 1

    for ejecutable, pids in procesos.items():
        politica = estado['politicas'].get(ejecutable)
        acumulado_previo = estado['acumulado'].get(ejecutable, 0)

        if _debe_bloquear(politica, acumulado_previo):
            for pid in pids:
                enforcement.terminar_proceso(pid)
        else:
            estado['acumulado'][ejecutable] = acumulado_previo + intervalo_segundos

    estado['activos'] = list(activos_actuales)
    cache_local.guardar(estado)
    return estado
