from alembic import op
import sqlalchemy as sa

revision = '0001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('username', sa.String(length=80), nullable=False),
        sa.Column('password_hash', sa.String(length=200), nullable=False),
        sa.Column('role', sa.String(length=20), server_default='admin', nullable=False),
        sa.Column('totp_secret', sa.String(length=500), nullable=True),
        sa.Column('password_version', sa.Integer(), server_default='1', nullable=False),
        sa.Column('activo', sa.Boolean(), server_default=sa.true(), nullable=False),
        sa.Column('full_name', sa.String(length=150), nullable=True),
        sa.Column('position', sa.String(length=100), nullable=True),
        sa.Column('contact_info', sa.String(length=200), nullable=True),
        sa.Column('profile_pic', sa.String(length=255), nullable=True),
        sa.Column('permisos', sa.JSON(), nullable=True),
        sa.Column('last_seen', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('username'),
    )
    op.create_index('ix_users_activo', 'users', ['activo'], unique=False)
    op.create_index('ix_users_role', 'users', ['role'], unique=False)

    op.create_table(
        'audit_log',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user', sa.String(length=80), nullable=True),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('action', sa.String(length=200), nullable=True),
        sa.Column('entidad', sa.String(length=60), nullable=True),
        sa.Column('entidad_id', sa.Integer(), nullable=True),
        sa.Column('detalle', sa.JSON(), nullable=True),
        sa.Column('origen', sa.String(length=10), server_default='panel', nullable=False),
        sa.Column('ip', sa.String(length=45), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_audit_log_created_at', 'audit_log', ['created_at'], unique=False)
    op.create_index('ix_audit_log_entidad', 'audit_log', ['entidad'], unique=False)
    op.create_index('ix_audit_log_ip', 'audit_log', ['ip'], unique=False)
    op.create_index('ix_audit_log_user', 'audit_log', ['user'], unique=False)
    op.create_index('ix_audit_log_user_id', 'audit_log', ['user_id'], unique=False)

    op.create_table(
        'refresh_tokens',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('token_hash', sa.String(length=64), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('revoked', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_refresh_tokens_token_hash', 'refresh_tokens', ['token_hash'], unique=True)
    op.create_index('ix_refresh_tokens_user_id', 'refresh_tokens', ['user_id'], unique=False)

    op.create_table(
        'totp_backup_codes',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('code_hash', sa.String(length=64), nullable=False),
        sa.Column('consumed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_totp_backup_codes_code_hash', 'totp_backup_codes', ['code_hash'], unique=False)
    op.create_index('ix_totp_backup_codes_user_id', 'totp_backup_codes', ['user_id'], unique=False)


def downgrade():
    op.drop_index('ix_totp_backup_codes_user_id', table_name='totp_backup_codes')
    op.drop_index('ix_totp_backup_codes_code_hash', table_name='totp_backup_codes')
    op.drop_table('totp_backup_codes')

    op.drop_index('ix_refresh_tokens_user_id', table_name='refresh_tokens')
    op.drop_index('ix_refresh_tokens_token_hash', table_name='refresh_tokens')
    op.drop_table('refresh_tokens')

    op.drop_index('ix_audit_log_user_id', table_name='audit_log')
    op.drop_index('ix_audit_log_user', table_name='audit_log')
    op.drop_index('ix_audit_log_ip', table_name='audit_log')
    op.drop_index('ix_audit_log_entidad', table_name='audit_log')
    op.drop_index('ix_audit_log_created_at', table_name='audit_log')
    op.drop_table('audit_log')

    op.drop_index('ix_users_role', table_name='users')
    op.drop_index('ix_users_activo', table_name='users')
    op.drop_table('users')
