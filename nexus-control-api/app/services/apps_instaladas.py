from app.extensions import db
from app.models import AppInstalada


def reemplazar_inventario(equipo_id: int, entradas: list[dict]) -> int:
    AppInstalada.query.filter_by(equipo_id=equipo_id).delete()

    vistos = set()
    guardadas = 0
    for entrada in entradas:
        paquete = (entrada.get('paquete') or '').strip()
        etiqueta = (entrada.get('etiqueta') or '').strip()
        if not paquete or not etiqueta:
            continue
        if paquete in vistos:
            continue
        vistos.add(paquete)
        db.session.add(AppInstalada(equipo_id=equipo_id, paquete=paquete[:150], etiqueta=etiqueta[:150]))
        guardadas += 1

    return guardadas
