"""Initial migration: users, auth_tokens, verification_codes

Revision ID: 001_initial
Revises: 
Create Date: 2025-01-01 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '001_initial'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create users table
    op.create_table(
        'users',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('password_hash', sa.String(length=255), nullable=True),
        sa.Column('email_verified', sa.Boolean(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('role', sa.String(length=50), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_users_id'), 'users', ['id'], unique=False)
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)
    op.create_index(op.f('ix_users_role'), 'users', ['role'], unique=False)
    op.create_index(op.f('ix_users_deleted_at'), 'users', ['deleted_at'], unique=False)

    # Create auth_refresh_tokens table
    op.create_table(
        'auth_refresh_tokens',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('token_hash', sa.String(length=255), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('revoked_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('token_hash')
    )
    op.create_index(op.f('ix_auth_refresh_tokens_user_id'), 'auth_refresh_tokens', ['user_id'], unique=False)
    op.create_index(op.f('ix_auth_refresh_tokens_token_hash'), 'auth_refresh_tokens', ['token_hash'], unique=True)
    op.create_index(op.f('ix_auth_refresh_tokens_expires_at'), 'auth_refresh_tokens', ['expires_at'], unique=False)

    # Create verification_codes table
    op.create_table(
        'verification_codes',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('code', sa.String(length=6), nullable=False),
        sa.Column('code_type', sa.String(length=50), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('used_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_verification_codes_user_id'), 'verification_codes', ['user_id'], unique=False)
    op.create_index(op.f('ix_verification_codes_code'), 'verification_codes', ['code'], unique=False)
    op.create_index(op.f('ix_verification_codes_code_type'), 'verification_codes', ['code_type'], unique=False)
    op.create_index(op.f('ix_verification_codes_expires_at'), 'verification_codes', ['expires_at'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_verification_codes_expires_at'), table_name='verification_codes')
    op.drop_index(op.f('ix_verification_codes_code_type'), table_name='verification_codes')
    op.drop_index(op.f('ix_verification_codes_code'), table_name='verification_codes')
    op.drop_index(op.f('ix_verification_codes_user_id'), table_name='verification_codes')
    op.drop_table('verification_codes')
    op.drop_index(op.f('ix_auth_refresh_tokens_expires_at'), table_name='auth_refresh_tokens')
    op.drop_index(op.f('ix_auth_refresh_tokens_token_hash'), table_name='auth_refresh_tokens')
    op.drop_index(op.f('ix_auth_refresh_tokens_user_id'), table_name='auth_refresh_tokens')
    op.drop_table('auth_refresh_tokens')
    op.drop_index(op.f('ix_users_deleted_at'), table_name='users')
    op.drop_index(op.f('ix_users_role'), table_name='users')
    op.drop_index(op.f('ix_users_email'), table_name='users')
    op.drop_index(op.f('ix_users_id'), table_name='users')
    op.drop_table('users')

