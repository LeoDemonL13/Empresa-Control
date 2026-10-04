from alembic import op
import sqlalchemy as sa

revision = '0006'
down_revision = '0005'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        'metricas_sociales',
        sa.Column('origen', sa.String(length=20), server_default='manual', nullable=False),
    )

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


def downgrade():
    op.drop_index('ix_conexiones_sociales_plataforma', table_name='conexiones_sociales')
    op.drop_table('conexiones_sociales')
    op.drop_column('metricas_sociales', 'origen')
