from app.extensions import EncryptedJSON, db
from app.models._base import _now_utc

PLATAFORMAS_SOCIALES = ('facebook', 'instagram', 'tiktok', 'youtube', 'x')


class ConexionRedSocial(db.Model):
    __tablename__ = "conexiones_sociales"

    id = db.Column(db.Integer, primary_key=True)
    plataforma = db.Column(db.String(20), nullable=False, unique=True, index=True)
    credenciales_cifradas = db.Column(EncryptedJSON, nullable=True)
    ultima_sincronizacion = db.Column(db.DateTime(timezone=True), nullable=True)
    ultimo_error = db.Column(db.Text, nullable=True)
    actualizado_por = db.Column(db.String(80), nullable=True)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=_now_utc)
    updated_at = db.Column(db.DateTime(timezone=True), nullable=False, default=_now_utc, onupdate=_now_utc)
