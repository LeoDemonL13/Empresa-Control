from app.extensions import db
from app.models._base import _now_utc


class MetricaSocial(db.Model):
    __tablename__ = "metricas_sociales"

    id = db.Column(db.Integer, primary_key=True)
    red_social = db.Column(db.String(60), nullable=False)
    red_social_normalizada = db.Column(db.String(60), nullable=False, unique=True, index=True)
    me_gusta = db.Column(db.Integer, nullable=False, default=0, server_default='0')
    interacciones = db.Column(db.Integer, nullable=False, default=0, server_default='0')
    impresiones = db.Column(db.Integer, nullable=False, default=0, server_default='0')
    engagement = db.Column(db.Float, nullable=False, default=0, server_default='0')
    actualizado_por = db.Column(db.String(80), nullable=True)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=_now_utc)
    updated_at = db.Column(db.DateTime(timezone=True), nullable=False, default=_now_utc, onupdate=_now_utc)
