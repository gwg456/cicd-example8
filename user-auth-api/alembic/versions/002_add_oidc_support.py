"""Add OIDC support

Revision ID: 002
Revises: 001
Create Date: 2024-01-01 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '002'
down_revision = '001'
branch_labels = None
depends_on = None


def upgrade():
    # Add is_oidc_user column to users table
    op.add_column('users', sa.Column('is_oidc_user', sa.Boolean(), nullable=False, server_default='false'))
    
    # Make hashed_password nullable for OIDC users
    op.alter_column('users', 'hashed_password', nullable=True)
    
    # Create user_oidc_links table
    op.create_table('user_oidc_links',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('provider', sa.String(), nullable=False),
        sa.Column('provider_user_id', sa.String(), nullable=False),
        sa.Column('provider_data', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('provider', 'provider_user_id', name='_provider_user_uc')
    )
    op.create_index(op.f('ix_user_oidc_links_id'), 'user_oidc_links', ['id'], unique=False)
    op.create_index(op.f('ix_user_oidc_links_provider'), 'user_oidc_links', ['provider'], unique=False)
    op.create_index(op.f('ix_user_oidc_links_user_id'), 'user_oidc_links', ['user_id'], unique=False)
    
    # Create oidc_sessions table for temporary session storage
    op.create_table('oidc_sessions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('session_id', sa.String(), nullable=False),
        sa.Column('state', sa.String(), nullable=False),
        sa.Column('nonce', sa.String(), nullable=False),
        sa.Column('code_verifier', sa.String(), nullable=True),
        sa.Column('provider', sa.String(), nullable=False),
        sa.Column('redirect_uri', sa.String(), nullable=True),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_oidc_sessions_id'), 'oidc_sessions', ['id'], unique=False)
    op.create_index(op.f('ix_oidc_sessions_session_id'), 'oidc_sessions', ['session_id'], unique=True)


def downgrade():
    # Drop tables and indexes
    op.drop_index(op.f('ix_oidc_sessions_session_id'), table_name='oidc_sessions')
    op.drop_index(op.f('ix_oidc_sessions_id'), table_name='oidc_sessions')
    op.drop_table('oidc_sessions')
    
    op.drop_index(op.f('ix_user_oidc_links_user_id'), table_name='user_oidc_links')
    op.drop_index(op.f('ix_user_oidc_links_provider'), table_name='user_oidc_links')
    op.drop_index(op.f('ix_user_oidc_links_id'), table_name='user_oidc_links')
    op.drop_table('user_oidc_links')
    
    # Remove is_oidc_user column
    op.drop_column('users', 'is_oidc_user')
    
    # Make hashed_password not nullable again
    op.alter_column('users', 'hashed_password', nullable=False)