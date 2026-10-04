from alembic import op
import sqlalchemy as sa

revision = '0002'
down_revision = '0001'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'categorias',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('nombre', sa.String(length=80), nullable=False),
        sa.Column('nombre_normalizado', sa.String(length=80), nullable=False),
        sa.Column('created_by', sa.String(length=80), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_categorias_nombre_normalizado', 'categorias', ['nombre_normalizado'], unique=True)

    op.create_table(
        'equipos',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('nombre', sa.String(length=120), nullable=False),
        sa.Column('hostname', sa.String(length=120), nullable=True),
        sa.Column('ip', sa.String(length=45), nullable=True),
        sa.Column('mac', sa.String(length=17), nullable=True),
        sa.Column('usuario_asignado', sa.String(length=120), nullable=True),
        sa.Column('sistema_operativo', sa.String(length=60), nullable=True),
        sa.Column('agente_version', sa.String(length=30), nullable=True),
        sa.Column('categoria_id', sa.Integer(), nullable=True),
        sa.Column('api_key_hash', sa.String(length=64), nullable=True),
        sa.Column('api_key_prefijo', sa.String(length=12), nullable=True),
        sa.Column('politica_version', sa.Integer(), server_default='1', nullable=False),
        sa.Column('ultimo_latido', sa.DateTime(timezone=True), nullable=True),
        sa.Column('activo', sa.Boolean(), server_default=sa.true(), nullable=False),
        sa.Column('created_by', sa.String(length=80), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['categoria_id'], ['categorias.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('api_key_hash'),
        sa.UniqueConstraint('mac'),
    )
    op.create_index('ix_equipos_activo', 'equipos', ['activo'], unique=False)
    op.create_index('ix_equipos_categoria_id', 'equipos', ['categoria_id'], unique=False)

    op.create_table(
        'codigos_enrolamiento',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('equipo_id', sa.Integer(), nullable=False),
        sa.Column('codigo_hash', sa.String(length=64), nullable=False),
        sa.Column('expira_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('usado_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('creado_por', sa.String(length=80), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['equipo_id'], ['equipos.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_codigos_enrolamiento_codigo_hash', 'codigos_enrolamiento', ['codigo_hash'], unique=False)
    op.create_index('ix_codigos_enrolamiento_equipo_id', 'codigos_enrolamiento', ['equipo_id'], unique=False)


def downgrade():
    op.drop_index('ix_codigos_enrolamiento_equipo_id', table_name='codigos_enrolamiento')
    op.drop_index('ix_codigos_enrolamiento_codigo_hash', table_name='codigos_enrolamiento')
    op.drop_table('codigos_enrolamiento')

    op.drop_index('ix_equipos_categoria_id', table_name='equipos')
    op.drop_index('ix_equipos_activo', table_name='equipos')
    op.drop_table('equipos')

    op.drop_index('ix_categorias_nombre_normalizado', table_name='categorias')
    op.drop_table('categorias')
