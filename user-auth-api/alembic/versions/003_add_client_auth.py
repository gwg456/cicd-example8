"""Add client authentication support

Revision ID: 003
Revises: 002
Create Date: 2024-01-01 15:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '003'
down_revision = '002'
branch_labels = None
depends_on = None


def upgrade():
    # Create api_clients table
    op.create_table('api_clients',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('client_id', sa.String(), nullable=False),
        sa.Column('client_secret_hash', sa.String(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('owner_id', sa.Integer(), nullable=False),
        sa.Column('scopes', sa.ARRAY(sa.String()), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True, default=True),
        sa.Column('is_trusted', sa.Boolean(), nullable=True, default=False),
        sa.Column('last_used_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('request_count', sa.Integer(), nullable=True, default=0),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['owner_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_api_clients_client_id'), 'api_clients', ['client_id'], unique=True)
    op.create_index(op.f('ix_api_clients_id'), 'api_clients', ['id'], unique=False)
    op.create_index(op.f('ix_api_clients_owner_id'), 'api_clients', ['owner_id'], unique=False)
    
    # Create api_keys table
    op.create_table('api_keys',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('key_id', sa.String(), nullable=False),
        sa.Column('key_hash', sa.String(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('client_id', sa.Integer(), nullable=False),
        sa.Column('scopes', sa.ARRAY(sa.String()), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True, default=True),
        sa.Column('last_used_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('request_count', sa.Integer(), nullable=True, default=0),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['client_id'], ['api_clients.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_api_keys_id'), 'api_keys', ['id'], unique=False)
    op.create_index(op.f('ix_api_keys_key_id'), 'api_keys', ['key_id'], unique=True)
    
    # Create client_access_tokens table
    op.create_table('client_access_tokens',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('token_id', sa.String(), nullable=False),
        sa.Column('client_id', sa.String(), nullable=False),
        sa.Column('scopes', sa.ARRAY(sa.String()), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True, default=True),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('last_used_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['client_id'], ['api_clients.client_id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_client_access_tokens_id'), 'client_access_tokens', ['id'], unique=False)
    op.create_index(op.f('ix_client_access_tokens_token_id'), 'client_access_tokens', ['token_id'], unique=True)


def downgrade():
    # Drop tables and indexes
    op.drop_index(op.f('ix_client_access_tokens_token_id'), table_name='client_access_tokens')
    op.drop_index(op.f('ix_client_access_tokens_id'), table_name='client_access_tokens')
    op.drop_table('client_access_tokens')
    
    op.drop_index(op.f('ix_api_keys_key_id'), table_name='api_keys')
    op.drop_index(op.f('ix_api_keys_id'), table_name='api_keys')
    op.drop_table('api_keys')
    
    op.drop_index(op.f('ix_api_clients_owner_id'), table_name='api_clients')
    op.drop_index(op.f('ix_api_clients_id'), table_name='api_clients')
    op.drop_index(op.f('ix_api_clients_client_id'), table_name='api_clients')
    op.drop_table('api_clients')