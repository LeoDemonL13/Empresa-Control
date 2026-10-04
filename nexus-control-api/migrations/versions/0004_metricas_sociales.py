from alembic import op
import sqlalchemy as sa

revision = '0004'
down_revision = '0003'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'metricas_sociales',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('red_social', sa.String(length=60), nullable=False),
        sa.Column('red_social_normalizada', sa.String(length=60), nullable=False),
        sa.Column('me_gusta', sa.Integer(), server_default='0', nullable=False),
        sa.Column('interacciones', sa.Integer(), server_default='0', nullable=False),
        sa.Column('impresiones', sa.Integer(), server_default='0', nullable=False),
        sa.Column('engagement', sa.Float(), server_default='0', nullable=False),
        sa.Column('actualizado_por', sa.String(length=80), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(
        'ix_metricas_sociales_red_social_normalizada', 'metricas_sociales', ['red_social_normalizada'], unique=True,
    )


def downgrade():
    op.drop_index('ix_metricas_sociales_red_social_normalizada', table_name='metricas_sociales')
    op.drop_table('metricas_sociales')
