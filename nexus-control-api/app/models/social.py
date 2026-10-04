from sqlalchemy import true

from app.extensions import SocialEncryptedString, db
from app.models._base import _now_utc

PLATAFORMAS_SOCIALES = ('facebook', 'instagram', 'tiktok', 'youtube')

ESTADO_CONECTADO = 'CONNECTED'
ESTADO_REFRESCANDO = 'REFRESHING'
ESTADO_POR_EXPIRAR = 'TOKEN_EXPIRING'
ESTADO_REAUTH_REQUERIDA = 'REAUTH_REQUIRED'
ESTADO_ERROR = 'ERROR'
ESTADO_DESCONECTADO = 'DISCONNECTED'

ESTADOS_CONEXION = (
    ESTADO_CONECTADO, ESTADO_REFRESCANDO, ESTADO_POR_EXPIRAR,
    ESTADO_REAUTH_REQUERIDA, ESTADO_ERROR, ESTADO_DESCONECTADO,
)

DISPARADORES_SYNC = ('programado', 'manual')
ESTADOS_SYNC_RUN = ('running', 'ok', 'error')

TIPOS_ERROR_SYNC = (
    'temporal', 'timeout', 'limite_tasa', 'servidor_caido', 'token_expirado',
    'refresh_expirado', 'permisos_revocados', 'cuenta_eliminada',
    'api_deshabilitada', 'desconocido',
)


class SocialConnection(db.Model):
    __tablename__ = "social_connections"

    id = db.Column(db.Integer, primary_key=True)
    plataforma = db.Column(db.String(20), nullable=False, unique=True, index=True)
    estado = db.Column(db.String(20), nullable=False, default=ESTADO_DESCONECTADO, server_default=ESTADO_DESCONECTADO)

    access_token_cifrado = db.Column(SocialEncryptedString, nullable=True)
    refresh_token_cifrado = db.Column(SocialEncryptedString, nullable=True)
    tipo_token = db.Column(db.String(30), nullable=True)
    alcance = db.Column(db.Text, nullable=True)

    expira_at = db.Column(db.DateTime(timezone=True), nullable=True)
    refresh_expira_at = db.Column(db.DateTime(timezone=True), nullable=True)

    id_externo_usuario = db.Column(db.String(120), nullable=True)
    etiqueta_externa = db.Column(db.String(200), nullable=True)

    ultimo_error = db.Column(db.Text, nullable=True)
    ultimo_error_detalle = db.Column(db.Text, nullable=True)
    ultimo_error_tipo = db.Column(db.String(40), nullable=True)
    errores_consecutivos = db.Column(db.Integer, nullable=False, default=0, server_default='0')
    proximo_reintento_at = db.Column(db.DateTime(timezone=True), nullable=True)
    bloqueado_hasta = db.Column(db.DateTime(timezone=True), nullable=True)

    ultima_sincronizacion_at = db.Column(db.DateTime(timezone=True), nullable=True)
    proxima_sincronizacion_at = db.Column(db.DateTime(timezone=True), nullable=True)

    conectado_por = db.Column(db.String(80), nullable=True)
    conectado_at = db.Column(db.DateTime(timezone=True), nullable=True)

    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=_now_utc)
    updated_at = db.Column(db.DateTime(timezone=True), nullable=False, default=_now_utc, onupdate=_now_utc)

    cuentas = db.relationship(
        'SocialAccount', back_populates='conexion', cascade='all, delete-orphan',
        order_by='SocialAccount.id',
    )

    def conectada(self) -> bool:
        return bool(self.access_token_cifrado) and self.estado not in (ESTADO_DESCONECTADO, ESTADO_REAUTH_REQUERIDA)


class SocialAccount(db.Model):
    __tablename__ = "social_accounts"
    __table_args__ = (
        db.UniqueConstraint('plataforma', 'id_externo', name='ux_social_accounts_plataforma_externo'),
    )

    id = db.Column(db.Integer, primary_key=True)
    connection_id = db.Column(
        db.Integer, db.ForeignKey('social_connections.id', ondelete='CASCADE'), nullable=False, index=True,
    )
    plataforma = db.Column(db.String(20), nullable=False, index=True)
    id_externo = db.Column(db.String(120), nullable=False)
    nombre = db.Column(db.String(200), nullable=False)
    usuario = db.Column(db.String(120), nullable=True)
    url_imagen = db.Column(db.String(500), nullable=True)
    seguimiento_activo = db.Column(db.Boolean, nullable=False, default=True, server_default=true())
    metadatos_json = db.Column(db.JSON, nullable=True)

    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=_now_utc)
    updated_at = db.Column(db.DateTime(timezone=True), nullable=False, default=_now_utc, onupdate=_now_utc)

    conexion = db.relationship('SocialConnection', back_populates='cuentas')
    posts = db.relationship(
        'SocialPost', back_populates='cuenta', cascade='all, delete-orphan', order_by='SocialPost.id',
    )


class SocialPost(db.Model):
    __tablename__ = "social_posts"
    __table_args__ = (
        db.UniqueConstraint('plataforma', 'id_externo_post', name='ux_social_posts_plataforma_externo'),
    )

    id = db.Column(db.Integer, primary_key=True)
    account_id = db.Column(
        db.Integer, db.ForeignKey('social_accounts.id', ondelete='CASCADE'), nullable=False, index=True,
    )
    plataforma = db.Column(db.String(20), nullable=False, index=True)
    id_externo_post = db.Column(db.String(150), nullable=False)
    tipo = db.Column(db.String(30), nullable=True)
    permalink = db.Column(db.String(500), nullable=True)
    extracto = db.Column(db.Text, nullable=True)
    publicado_at = db.Column(db.DateTime(timezone=True), nullable=True, index=True)

    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=_now_utc)
    updated_at = db.Column(db.DateTime(timezone=True), nullable=False, default=_now_utc, onupdate=_now_utc)

    cuenta = db.relationship('SocialAccount', back_populates='posts')
    metricas = db.relationship(
        'SocialPostMetric', back_populates='post', uselist=False, cascade='all, delete-orphan',
    )


class SocialPostMetric(db.Model):
    __tablename__ = "social_post_metrics"

    id = db.Column(db.Integer, primary_key=True)
    post_id = db.Column(
        db.Integer, db.ForeignKey('social_posts.id', ondelete='CASCADE'), nullable=False, unique=True, index=True,
    )
    me_gusta = db.Column(db.Integer, nullable=True)
    comentarios = db.Column(db.Integer, nullable=True)
    compartidos = db.Column(db.Integer, nullable=True)
    vistas = db.Column(db.Integer, nullable=True)
    impresiones = db.Column(db.Integer, nullable=True)
    tasa_engagement = db.Column(db.Float, nullable=True)
    capturado_at = db.Column(db.DateTime(timezone=True), nullable=True)

    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=_now_utc)
    updated_at = db.Column(db.DateTime(timezone=True), nullable=False, default=_now_utc, onupdate=_now_utc)

    post = db.relationship('SocialPost', back_populates='metricas')


class SocialMetricSnapshot(db.Model):
    __tablename__ = "social_metric_snapshots"
    __table_args__ = (
        db.Index('ix_social_metric_snapshots_cuenta', 'account_id', 'nombre_metrica', 'capturado_at'),
        db.Index('ix_social_metric_snapshots_post', 'post_id', 'nombre_metrica', 'capturado_at'),
    )

    id = db.Column(db.Integer, primary_key=True)
    connection_id = db.Column(
        db.Integer, db.ForeignKey('social_connections.id', ondelete='CASCADE'), nullable=True, index=True,
    )
    account_id = db.Column(
        db.Integer, db.ForeignKey('social_accounts.id', ondelete='CASCADE'), nullable=True,
    )
    post_id = db.Column(
        db.Integer, db.ForeignKey('social_posts.id', ondelete='CASCADE'), nullable=True,
    )
    plataforma = db.Column(db.String(20), nullable=False, index=True)
    nombre_metrica = db.Column(db.String(40), nullable=False)
    valor = db.Column(db.Float, nullable=True)
    capturado_at = db.Column(db.DateTime(timezone=True), nullable=False, index=True)

    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=_now_utc)


class SocialSyncRun(db.Model):
    __tablename__ = "social_sync_runs"

    id = db.Column(db.Integer, primary_key=True)
    connection_id = db.Column(
        db.Integer, db.ForeignKey('social_connections.id', ondelete='SET NULL'), nullable=True, index=True,
    )
    plataforma = db.Column(db.String(20), nullable=False, index=True)
    iniciado_at = db.Column(db.DateTime(timezone=True), nullable=False, default=_now_utc, index=True)
    finalizado_at = db.Column(db.DateTime(timezone=True), nullable=True)
    estado = db.Column(db.String(20), nullable=False, default='running', server_default='running')
    tipo_error = db.Column(db.String(40), nullable=True)
    error_mensaje = db.Column(db.Text, nullable=True)
    error_detalle = db.Column(db.Text, nullable=True)
    elementos_actualizados = db.Column(db.Integer, nullable=False, default=0, server_default='0')
    tiempo_respuesta_ms = db.Column(db.Integer, nullable=True)
    disparado_por = db.Column(db.String(20), nullable=False, default='programado', server_default='programado')
    usuario = db.Column(db.String(80), nullable=True)

    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=_now_utc)


class SocialDailySummary(db.Model):
    __tablename__ = "social_daily_summaries"
    __table_args__ = (
        db.UniqueConstraint('account_id', 'fecha', name='ux_social_daily_summaries_cuenta_fecha'),
    )

    id = db.Column(db.Integer, primary_key=True)
    account_id = db.Column(
        db.Integer, db.ForeignKey('social_accounts.id', ondelete='CASCADE'), nullable=False, index=True,
    )
    plataforma = db.Column(db.String(20), nullable=False, index=True)
    fecha = db.Column(db.Date, nullable=False, index=True)

    seguidores_fin = db.Column(db.Integer, nullable=True)
    cambio_seguidores = db.Column(db.Integer, nullable=True)
    publicaciones_nuevas = db.Column(db.Integer, nullable=False, default=0, server_default='0')
    total_me_gusta = db.Column(db.Integer, nullable=True)
    total_comentarios = db.Column(db.Integer, nullable=True)
    total_compartidos = db.Column(db.Integer, nullable=True)
    total_vistas = db.Column(db.Integer, nullable=True)
    tasa_engagement_promedio = db.Column(db.Float, nullable=True)
    mejor_post_id = db.Column(db.Integer, db.ForeignKey('social_posts.id', ondelete='SET NULL'), nullable=True)
    peor_post_id = db.Column(db.Integer, db.ForeignKey('social_posts.id', ondelete='SET NULL'), nullable=True)

    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=_now_utc)
    updated_at = db.Column(db.DateTime(timezone=True), nullable=False, default=_now_utc, onupdate=_now_utc)


class SocialOAuthState(db.Model):
    __tablename__ = "social_oauth_states"

    id = db.Column(db.Integer, primary_key=True)
    estado = db.Column(db.String(64), nullable=False, unique=True, index=True)
    plataforma = db.Column(db.String(20), nullable=False)
    usuario_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    code_verifier = db.Column(db.String(128), nullable=True)
    redirect_uri = db.Column(db.String(300), nullable=False)

    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=_now_utc)
    expira_at = db.Column(db.DateTime(timezone=True), nullable=False, index=True)
