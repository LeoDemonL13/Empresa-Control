from alembic import op
import sqlalchemy as sa

revision = '0003'
down_revision = '0002'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'aplicaciones',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('nombre', sa.String(length=150), nullable=False),
        sa.Column('ejecutable', sa.String(length=150), nullable=False),
        sa.Column('ejecutable_normalizado', sa.String(length=150), nullable=False),
        sa.Column('editor', sa.String(length=120), nullable=True),
        sa.Column('ruta_tipica', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_aplicaciones_ejecutable_normalizado', 'aplicaciones', ['ejecutable_normalizado'], unique=True)

    op.create_table(
        'equipo_app_politica',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('equipo_id', sa.Integer(), nullable=False),
        sa.Column('aplicacion_id', sa.Integer(), nullable=False),
        sa.Column('instalada', sa.Boolean(), server_default=sa.true(), nullable=False),
        sa.Column('estado', sa.String(length=20), server_default='permitida', nullable=False),
        sa.Column('tipo_uso', sa.String(length=20), server_default='sin_limite', nullable=False),
        sa.Column('limite_minutos', sa.Integer(), nullable=True),
        sa.Column('periodo', sa.String(length=20), server_default='diario', nullable=False),
        sa.Column('actualizada_por', sa.String(length=80), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['equipo_id'], ['equipos.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['aplicacion_id'], ['aplicaciones.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('equipo_id', 'aplicacion_id', name='uq_equipo_app_politica'),
    )
    op.create_index('ix_equipo_app_politica_equipo_id', 'equipo_app_politica', ['equipo_id'], unique=False)
    op.create_index('ix_equipo_app_politica_aplicacion_id', 'equipo_app_politica', ['aplicacion_id'], unique=False)

    op.create_table(
        'uso_aplicacion',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('equipo_id', sa.Integer(), nullable=False),
        sa.Column('aplicacion_id', sa.Integer(), nullable=False),
        sa.Column('fecha', sa.Date(), nullable=False),
        sa.Column('segundos', sa.Integer(), server_default='0', nullable=False),
        sa.Column('sesiones', sa.Integer(), server_default='0', nullable=False),
        sa.ForeignKeyConstraint(['equipo_id'], ['equipos.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['aplicacion_id'], ['aplicaciones.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('equipo_id', 'aplicacion_id', 'fecha', name='uq_uso_aplicacion_dia'),
    )
    op.create_index('ix_uso_aplicacion_equipo_id', 'uso_aplicacion', ['equipo_id'], unique=False)
    op.create_index('ix_uso_aplicacion_aplicacion_id', 'uso_aplicacion', ['aplicacion_id'], unique=False)
    op.create_index('ix_uso_aplicacion_fecha', 'uso_aplicacion', ['fecha'], unique=False)


def downgrade():
    op.drop_index('ix_uso_aplicacion_fecha', table_name='uso_aplicacion')
    op.drop_index('ix_uso_aplicacion_aplicacion_id', table_name='uso_aplicacion')
    op.drop_index('ix_uso_aplicacion_equipo_id', table_name='uso_aplicacion')
    op.drop_table('uso_aplicacion')

    op.drop_index('ix_equipo_app_politica_aplicacion_id', table_name='equipo_app_politica')
    op.drop_index('ix_equipo_app_politica_equipo_id', table_name='equipo_app_politica')
    op.drop_table('equipo_app_politica')

    op.drop_index('ix_aplicaciones_ejecutable_normalizado', table_name='aplicaciones')
    op.drop_table('aplicaciones')
