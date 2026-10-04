from sqlalchemy import true

from app.extensions import db, EncryptedString
from app.models._base import _now_utc


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='admin', server_default='admin', index=True)
    totp_secret = db.Column(EncryptedString(500), nullable=True)
    password_version = db.Column(db.Integer, nullable=False, default=1, server_default='1')
    activo = db.Column(db.Boolean, nullable=False, default=True, server_default=true(), index=True)
    full_name = db.Column(db.String(150), nullable=True)
    position = db.Column(db.String(100), nullable=True)
    contact_info = db.Column(db.String(200), nullable=True)
    profile_pic = db.Column(db.String(255), nullable=True, default='default.png')
    permisos = db.Column(db.JSON, nullable=True)
    last_seen = db.Column(db.DateTime, nullable=True, default=None)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=_now_utc)


class RefreshToken(db.Model):
    __tablename__ = "refresh_tokens"

    id = db.Column(db.Integer, primary_key=True)
    token_hash = db.Column(db.String(64), unique=True, nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    expires_at = db.Column(db.DateTime(timezone=True), nullable=False)
    revoked = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), default=_now_utc)

    user = db.relationship(
        'User',
        backref=db.backref('refresh_tokens', lazy=True, cascade='all, delete-orphan'),
    )


class TwoFactorBackupCode(db.Model):
    __tablename__ = "totp_backup_codes"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    code_hash = db.Column(db.String(64), nullable=False, index=True)
    consumed_at = db.Column(db.DateTime(timezone=True), nullable=True)
    created_at = db.Column(db.DateTime(timezone=True), default=_now_utc)

    user = db.relationship(
        'User',
        backref=db.backref('backup_codes', lazy=True, cascade='all, delete-orphan'),
    )


class AuditLog(db.Model):
    __tablename__ = "audit_log"

    id = db.Column(db.Integer, primary_key=True)
    user = db.Column(db.String(80), index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='SET NULL'), nullable=True, index=True)
    action = db.Column(db.String(200))
    entidad = db.Column(db.String(60), nullable=True, index=True)
    entidad_id = db.Column(db.Integer, nullable=True)
    detalle = db.Column(db.JSON, nullable=True)
    origen = db.Column(db.String(10), nullable=False, default='panel', server_default='panel')
    ip = db.Column(db.String(45), index=True)
    created_at = db.Column(db.DateTime, default=_now_utc, index=True)
