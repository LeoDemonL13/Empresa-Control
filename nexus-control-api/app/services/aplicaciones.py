from app.extensions import db
from app.models import Aplicacion
from app.models._base import _now_utc


def obtener_o_crear(ejecutable: str, nombre: str | None = None, ruta_tipica: str | None = None):
    ejecutable = (ejecutable or '').strip()
    if not ejecutable:
        return None, False

    normalizado = ejecutable.lower()
    existente = Aplicacion.query.filter_by(ejecutable_normalizado=normalizado).first()
    if existente:
        return existente, False

    nueva = Aplicacion(
        nombre=(nombre or ejecutable).strip(),
        ejecutable=ejecutable,
        ejecutable_normalizado=normalizado,
        ruta_tipica=(ruta_tipica or '').strip() or None,
        created_at=_now_utc(),
    )
    db.session.add(nueva)
    db.session.flush()
    return nueva, True
