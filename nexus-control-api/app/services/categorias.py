from app.extensions import db
from app.models import Categoria
from app.models._base import _now_utc


def obtener_o_crear(nombre: str, creado_por: str | None):
    nombre = (nombre or '').strip()
    if not nombre:
        return None, False

    normalizado = nombre.lower()
    existente = Categoria.query.filter_by(nombre_normalizado=normalizado).first()
    if existente:
        return existente, False

    nueva = Categoria(nombre=nombre, nombre_normalizado=normalizado, created_by=creado_por, created_at=_now_utc())
    db.session.add(nueva)
    db.session.flush()
    return nueva, True
