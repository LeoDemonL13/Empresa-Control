from alembic import op
import sqlalchemy as sa

revision = '0007'
down_revision = '0006'
branch_labels = None
depends_on = None


def upgrade():
    op.drop_index('ix_conexiones_sociales_plataforma', table_name='conexiones_sociales')
    op.drop_table('conexiones_sociales')

    op.create_table(
        'social_connections',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('plataforma', sa.String(length=20), nullable=False),
        sa.Column('estado', sa.String(length=20), server_default='DISCONNECTED', nullable=False),
        sa.Column('access_token_cifrado', sa.Text(), nullable=True),
        sa.Column('refresh_token_cifrado', sa.Text(), nullable=True),
        sa.Column('tipo_token', sa.String(length=30), nullable=True),
        sa.Column('alcance', sa.Text(), nullable=True),
        sa.Column('expira_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('refresh_expira_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('id_externo_usuario', sa.String(length=120), nullable=True),
        sa.Column('etiqueta_externa', sa.String(length=200), nullable=True),
        sa.Column('ultimo_error', sa.Text(), nullable=True),
        sa.Column('ultimo_error_detalle', sa.Text(), nullable=True),
        sa.Column('ultimo_error_tipo', sa.String(length=40), nullable=True),
        sa.Column('errores_consecutivos', sa.Integer(), server_default='0', nullable=False),
        sa.Column('proximo_reintento_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('bloqueado_hasta', sa.DateTime(timezone=True), nullable=True),
        sa.Column('ultima_sincronizacion_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('proxima_sincronizacion_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('conectado_por', sa.String(length=80), nullable=True),
        sa.Column('conectado_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(
        'ix_social_connections_plataforma', 'social_connections', ['plataforma'], unique=True,
    )

    op.create_table(
        'social_accounts',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('connection_id', sa.Integer(), nullable=False),
        sa.Column('plataforma', sa.String(length=20), nullable=False),
        sa.Column('id_externo', sa.String(length=120), nullable=False),
        sa.Column('nombre', sa.String(length=200), nullable=False),
        sa.Column('usuario', sa.String(length=120), nullable=True),
        sa.Column('url_imagen', sa.String(length=500), nullable=True),
        sa.Column('seguimiento_activo', sa.Boolean(), server_default=sa.true(), nullable=False),
        sa.Column('metadatos_json', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['connection_id'], ['social_connections.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('plataforma', 'id_externo', name='ux_social_accounts_plataforma_externo'),
    )
    op.create_index('ix_social_accounts_connection_id', 'social_accounts', ['connection_id'])
    op.create_index('ix_social_accounts_plataforma', 'social_accounts', ['plataforma'])

    op.create_table(
        'social_posts',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('account_id', sa.Integer(), nullable=False),
        sa.Column('plataforma', sa.String(length=20), nullable=False),
        sa.Column('id_externo_post', sa.String(length=150), nullable=False),
        sa.Column('tipo', sa.String(length=30), nullable=True),
        sa.Column('permalink', sa.String(length=500), nullable=True),
        sa.Column('extracto', sa.Text(), nullable=True),
        sa.Column('publicado_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['account_id'], ['social_accounts.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('plataforma', 'id_externo_post', name='ux_social_posts_plataforma_externo'),
    )
    op.create_index('ix_social_posts_account_id', 'social_posts', ['account_id'])
    op.create_index('ix_social_posts_plataforma', 'social_posts', ['plataforma'])
    op.create_index('ix_social_posts_publicado_at', 'social_posts', ['publicado_at'])

    op.create_table(
        'social_post_metrics',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('post_id', sa.Integer(), nullable=False),
        sa.Column('me_gusta', sa.Integer(), nullable=True),
        sa.Column('comentarios', sa.Integer(), nullable=True),
        sa.Column('compartidos', sa.Integer(), nullable=True),
        sa.Column('vistas', sa.Integer(), nullable=True),
        sa.Column('impresiones', sa.Integer(), nullable=True),
        sa.Column('tasa_engagement', sa.Float(), nullable=True),
        sa.Column('capturado_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['post_id'], ['social_posts.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(
        'ix_social_post_metrics_post_id', 'social_post_metrics', ['post_id'], unique=True,
    )

    op.create_table(
        'social_metric_snapshots',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('connection_id', sa.Integer(), nullable=True),
        sa.Column('account_id', sa.Integer(), nullable=True),
        sa.Column('post_id', sa.Integer(), nullable=True),
        sa.Column('plataforma', sa.String(length=20), nullable=False),
        sa.Column('nombre_metrica', sa.String(length=40), nullable=False),
        sa.Column('valor', sa.Float(), nullable=True),
        sa.Column('capturado_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['connection_id'], ['social_connections.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['account_id'], ['social_accounts.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['post_id'], ['social_posts.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_social_metric_snapshots_connection_id', 'social_metric_snapshots', ['connection_id'])
    op.create_index('ix_social_metric_snapshots_plataforma', 'social_metric_snapshots', ['plataforma'])
    op.create_index('ix_social_metric_snapshots_capturado_at', 'social_metric_snapshots', ['capturado_at'])
    op.create_index(
        'ix_social_metric_snapshots_cuenta', 'social_metric_snapshots',
        ['account_id', 'nombre_metrica', 'capturado_at'],
    )
    op.create_index(
        'ix_social_metric_snapshots_post', 'social_metric_snapshots',
        ['post_id', 'nombre_metrica', 'capturado_at'],
    )

    op.create_table(
        'social_sync_runs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('connection_id', sa.Integer(), nullable=True),
        sa.Column('plataforma', sa.String(length=20), nullable=False),
        sa.Column('iniciado_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('finalizado_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('estado', sa.String(length=20), server_default='running', nullable=False),
        sa.Column('tipo_error', sa.String(length=40), nullable=True),
        sa.Column('error_mensaje', sa.Text(), nullable=True),
        sa.Column('error_detalle', sa.Text(), nullable=True),
        sa.Column('elementos_actualizados', sa.Integer(), server_default='0', nullable=False),
        sa.Column('tiempo_respuesta_ms', sa.Integer(), nullable=True),
        sa.Column('disparado_por', sa.String(length=20), server_default='programado', nullable=False),
        sa.Column('usuario', sa.String(length=80), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['connection_id'], ['social_connections.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_social_sync_runs_connection_id', 'social_sync_runs', ['connection_id'])
    op.create_index('ix_social_sync_runs_plataforma', 'social_sync_runs', ['plataforma'])
    op.create_index('ix_social_sync_runs_iniciado_at', 'social_sync_runs', ['iniciado_at'])

    op.create_table(
        'social_daily_summaries',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('account_id', sa.Integer(), nullable=False),
        sa.Column('plataforma', sa.String(length=20), nullable=False),
        sa.Column('fecha', sa.Date(), nullable=False),
        sa.Column('seguidores_fin', sa.Integer(), nullable=True),
        sa.Column('cambio_seguidores', sa.Integer(), nullable=True),
        sa.Column('publicaciones_nuevas', sa.Integer(), server_default='0', nullable=False),
        sa.Column('total_me_gusta', sa.Integer(), nullable=True),
        sa.Column('total_comentarios', sa.Integer(), nullable=True),
        sa.Column('total_compartidos', sa.Integer(), nullable=True),
        sa.Column('total_vistas', sa.Integer(), nullable=True),
        sa.Column('tasa_engagement_promedio', sa.Float(), nullable=True),
        sa.Column('mejor_post_id', sa.Integer(), nullable=True),
        sa.Column('peor_post_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['account_id'], ['social_accounts.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['mejor_post_id'], ['social_posts.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['peor_post_id'], ['social_posts.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('account_id', 'fecha', name='ux_social_daily_summaries_cuenta_fecha'),
    )
    op.create_index('ix_social_daily_summaries_account_id', 'social_daily_summaries', ['account_id'])
    op.create_index('ix_social_daily_summaries_plataforma', 'social_daily_summaries', ['plataforma'])
    op.create_index('ix_social_daily_summaries_fecha', 'social_daily_summaries', ['fecha'])

    op.create_table(
        'social_oauth_states',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('estado', sa.String(length=64), nullable=False),
        sa.Column('plataforma', sa.String(length=20), nullable=False),
        sa.Column('usuario_id', sa.Integer(), nullable=False),
        sa.Column('code_verifier', sa.String(length=128), nullable=True),
        sa.Column('redirect_uri', sa.String(length=300), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('expira_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['usuario_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_social_oauth_states_estado', 'social_oauth_states', ['estado'], unique=True)
    op.create_index('ix_social_oauth_states_usuario_id', 'social_oauth_states', ['usuario_id'])
    op.create_index('ix_social_oauth_states_expira_at', 'social_oauth_states', ['expira_at'])


def downgrade():
    op.drop_table('social_oauth_states')

    op.drop_index('ix_social_daily_summaries_fecha', table_name='social_daily_summaries')
    op.drop_index('ix_social_daily_summaries_plataforma', table_name='social_daily_summaries')
    op.drop_index('ix_social_daily_summaries_account_id', table_name='social_daily_summaries')
    op.drop_table('social_daily_summaries')

    op.drop_index('ix_social_sync_runs_iniciado_at', table_name='social_sync_runs')
    op.drop_index('ix_social_sync_runs_plataforma', table_name='social_sync_runs')
    op.drop_index('ix_social_sync_runs_connection_id', table_name='social_sync_runs')
    op.drop_table('social_sync_runs')

    op.drop_index('ix_social_metric_snapshots_post', table_name='social_metric_snapshots')
    op.drop_index('ix_social_metric_snapshots_cuenta', table_name='social_metric_snapshots')
    op.drop_index('ix_social_metric_snapshots_capturado_at', table_name='social_metric_snapshots')
    op.drop_index('ix_social_metric_snapshots_plataforma', table_name='social_metric_snapshots')
    op.drop_index('ix_social_metric_snapshots_connection_id', table_name='social_metric_snapshots')
    op.drop_table('social_metric_snapshots')

    op.drop_index('ix_social_post_metrics_post_id', table_name='social_post_metrics')
    op.drop_table('social_post_metrics')

    op.drop_index('ix_social_posts_publicado_at', table_name='social_posts')
    op.drop_index('ix_social_posts_plataforma', table_name='social_posts')
    op.drop_index('ix_social_posts_account_id', table_name='social_posts')
    op.drop_table('social_posts')

    op.drop_index('ix_social_accounts_plataforma', table_name='social_accounts')
    op.drop_index('ix_social_accounts_connection_id', table_name='social_accounts')
    op.drop_table('social_accounts')

    op.drop_index('ix_social_connections_plataforma', table_name='social_connections')
    op.drop_table('social_connections')

    op.create_table(
        'conexiones_sociales',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('plataforma', sa.String(length=20), nullable=False),
        sa.Column('credenciales_cifradas', sa.Text(), nullable=True),
        sa.Column('ultima_sincronizacion', sa.DateTime(timezone=True), nullable=True),
        sa.Column('ultimo_error', sa.Text(), nullable=True),
        sa.Column('actualizado_por', sa.String(length=80), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(
        'ix_conexiones_sociales_plataforma', 'conexiones_sociales', ['plataforma'], unique=True,
    )
