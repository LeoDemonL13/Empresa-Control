from sqlalchemy import true

from app.extensions import db
from app.models._base import _now_utc


class Categoria(db.Model):
    __tablename__ = "categorias"

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(80), nullable=False)
    nombre_normalizado = db.Column(db.String(80), nullable=False, unique=True, index=True)
    created_by = db.Column(db.String(80), nullable=True)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=_now_utc)

    equipos = db.relationship('Equipo', back_populates='categoria')


class Equipo(db.Model):
    __tablename__ = "equipos"

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(120), nullable=False)
    hostname = db.Column(db.String(120), nullable=True)
    ip = db.Column(db.String(45), nullable=True)
    mac = db.Column(db.String(17), nullable=True, unique=True)
    usuario_asignado = db.Column(db.String(120), nullable=True)
    sistema_operativo = db.Column(db.String(60), nullable=True)
    agente_version = db.Column(db.String(30), nullable=True)
    categoria_id = db.Column(db.Integer, db.ForeignKey('categorias.id', ondelete='SET NULL'), nullable=True, index=True)
    api_key_hash = db.Column(db.String(64), nullable=True, unique=True)
    api_key_prefijo = db.Column(db.String(12), nullable=True)
    politica_version = db.Column(db.Integer, nullable=False, default=1, server_default='1')
    ultimo_latido = db.Column(db.DateTime(timezone=True), nullable=True)
    activo = db.Column(db.Boolean, nullable=False, default=True, server_default=true(), index=True)
    created_by = db.Column(db.String(80), nullable=True)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=_now_utc)

    categoria = db.relationship('Categoria', back_populates='equipos')
    codigos_enrolamiento = db.relationship(
        'CodigoEnrolamiento', back_populates='equipo', cascade='all, delete-orphan',
    )


class CodigoEnrolamiento(db.Model):
    __tablename__ = "codigos_enrolamiento"

    id = db.Column(db.Integer, primary_key=True)
    equipo_id = db.Column(db.Integer, db.ForeignKey('equipos.id', ondelete='CASCADE'), nullable=False, index=True)
    codigo_hash = db.Column(db.String(64), nullable=False, index=True)
    expira_at = db.Column(db.DateTime(timezone=True), nullable=False)
    usado_at = db.Column(db.DateTime(timezone=True), nullable=True)
    creado_por = db.Column(db.String(80), nullable=True)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=_now_utc)

    equipo = db.relationship('Equipo', back_populates='codigos_enrolamiento')
