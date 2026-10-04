from app.extensions import db
from app.models import MetricaSocial


def obtener_o_crear(red_social: str):
    red_social = (red_social or '').strip()
    if not red_social:
        return None, False

    normalizada = red_social.lower()
    existente = MetricaSocial.query.filter_by(red_social_normalizada=normalizada).first()
    if existente:
        return existente, False

    nueva = MetricaSocial(red_social=red_social, red_social_normalizada=normalizada)
    db.session.add(nueva)
    db.session.flush()
    return nueva, True
