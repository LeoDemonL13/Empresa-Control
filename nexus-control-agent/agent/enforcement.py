import psutil


def terminar_proceso(pid: int) -> bool:
    try:
        proceso = psutil.Process(pid)
        proceso.terminate()
        try:
            proceso.wait(timeout=3)
        except psutil.TimeoutExpired:
            proceso.kill()
        return True
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        return False
