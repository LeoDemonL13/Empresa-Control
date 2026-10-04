from sqlalchemy import true

from app.constants import ESTADOS_APP, TIPOS_USO_APP
from app.extensions import db
from app.models._base import _now_utc


class Aplicacion(db.Model):
    __tablename__ = "aplicaciones"

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(150), nullable=False)
    ejecutable = db.Column(db.String(150), nullable=False)
    ejecutable_normalizado = db.Column(db.String(150), nullable=False, unique=True, index=True)
    editor = db.Column(db.String(120), nullable=True)
    ruta_tipica = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=_now_utc)

    politicas = db.relationship('EquipoAppPolitica', back_populates='aplicacion', cascade='all, delete-orphan')


class EquipoAppPolitica(db.Model):
    __tablename__ = "equipo_app_politica"

    id = db.Column(db.Integer, primary_key=True)
    equipo_id = db.Column(db.Integer, db.ForeignKey('equipos.id', ondelete='CASCADE'), nullable=False, index=True)
    aplicacion_id = db.Column(db.Integer, db.ForeignKey('aplicaciones.id', ondelete='CASCADE'), nullable=False, index=True)
    instalada = db.Column(db.Boolean, nullable=False, default=True, server_default=true())
    estado = db.Column(db.String(20), nullable=False, default=ESTADOS_APP[0], server_default=ESTADOS_APP[0])
    tipo_uso = db.Column(db.String(20), nullable=False, default=TIPOS_USO_APP[0], server_default=TIPOS_USO_APP[0])
    limite_minutos = db.Column(db.Integer, nullable=True)
    periodo = db.Column(db.String(20), nullable=False, default='diario', server_default='diario')
    actualizada_por = db.Column(db.String(80), nullable=True)
    updated_at = db.Column(db.DateTime(timezone=True), nullable=False, default=_now_utc, onupdate=_now_utc)

    equipo = db.relationship('Equipo')
    aplicacion = db.relationship('Aplicacion', back_populates='politicas')

    __table_args__ = (
        db.UniqueConstraint('equipo_id', 'aplicacion_id', name='uq_equipo_app_politica'),
    )


class UsoAplicacion(db.Model):
    __tablename__ = "uso_aplicacion"

    id = db.Column(db.Integer, primary_key=True)
    equipo_id = db.Column(db.Integer, db.ForeignKey('equipos.id', ondelete='CASCADE'), nullable=False, index=True)
    aplicacion_id = db.Column(db.Integer, db.ForeignKey('aplicaciones.id', ondelete='CASCADE'), nullable=False, index=True)
    fecha = db.Column(db.Date, nullable=False, index=True)
    segundos = db.Column(db.Integer, nullable=False, default=0, server_default='0')
    sesiones = db.Column(db.Integer, nullable=False, default=0, server_default='0')

    equipo = db.relationship('Equipo')
    aplicacion = db.relationship('Aplicacion')

    __table_args__ = (
        db.UniqueConstraint('equipo_id', 'aplicacion_id', 'fecha', name='uq_uso_aplicacion_dia'),
    )
