from alembic import op
import sqlalchemy as sa

revision = '0005'
down_revision = '0004'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('equipos', sa.Column('tipo', sa.String(length=10), server_default='pc', nullable=False))

    op.create_table(
        'apps_instaladas',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('equipo_id', sa.Integer(), nullable=False),
        sa.Column('paquete', sa.String(length=150), nullable=False),
        sa.Column('etiqueta', sa.String(length=150), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['equipo_id'], ['equipos.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('equipo_id', 'paquete', name='uq_apps_instaladas_equipo_paquete'),
    )
    op.create_index('ix_apps_instaladas_equipo_id', 'apps_instaladas', ['equipo_id'], unique=False)


def downgrade():
    op.drop_index('ix_apps_instaladas_equipo_id', table_name='apps_instaladas')
    op.drop_table('apps_instaladas')
    op.drop_column('equipos', 'tipo')
