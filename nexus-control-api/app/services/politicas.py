from app.extensions import db
from app.models import EquipoAppPolitica


def obtener_o_crear_politica(equipo_id: int, aplicacion_id: int):
    existente = EquipoAppPolitica.query.filter_by(equipo_id=equipo_id, aplicacion_id=aplicacion_id).first()
    if existente:
        return existente, False

    nueva = EquipoAppPolitica(equipo_id=equipo_id, aplicacion_id=aplicacion_id)
    db.session.add(nueva)
    db.session.flush()
    return nueva, True
