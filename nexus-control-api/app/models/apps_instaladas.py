from app.extensions import db
from app.models._base import _now_utc


class AppInstalada(db.Model):
    __tablename__ = "apps_instaladas"

    id = db.Column(db.Integer, primary_key=True)
    equipo_id = db.Column(db.Integer, db.ForeignKey('equipos.id', ondelete='CASCADE'), nullable=False, index=True)
    paquete = db.Column(db.String(150), nullable=False)
    etiqueta = db.Column(db.String(150), nullable=False)
    updated_at = db.Column(db.DateTime(timezone=True), nullable=False, default=_now_utc, onupdate=_now_utc)

    equipo = db.relationship('Equipo')

    __table_args__ = (
        db.UniqueConstraint('equipo_id', 'paquete', name='uq_apps_instaladas_equipo_paquete'),
    )
