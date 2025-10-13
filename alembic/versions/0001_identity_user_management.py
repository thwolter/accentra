"""Add identity schema for user management."""

from __future__ import annotations

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from sqlalchemy.sql import func

from alembic import op

revision = '0002_identity_user_management'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute('CREATE SCHEMA IF NOT EXISTS identity;')

    op.create_table(
        'tenants',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('name', sa.String(length=255), nullable=False, unique=True),
        sa.Column('plan', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(timezone=False), nullable=False, server_default=func.now()),
        sa.Column(
            'updated_at',
            sa.TIMESTAMP(),
            nullable=False,
            server_default=func.now(),
            server_onupdate=func.now(),
        ),
        schema='identity',
    )

    op.create_table(
        'users',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('email', sa.String(length=255), nullable=False, unique=True),
        sa.Column('full_name', sa.String(length=255), nullable=True),
        sa.Column('hashed_password', sa.String(length=512), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('TRUE')),
        sa.Column('created_at', sa.TIMESTAMP(timezone=False), nullable=False, server_default=func.now()),
        sa.Column(
            'updated_at',
            sa.TIMESTAMP(),
            nullable=False,
            server_default=func.now(),
            server_onupdate=func.now(),
        ),
        schema='identity',
    )
    op.create_index('ix_identity_users_email', 'users', ['email'], unique=True, schema='identity')

    role_enum = postgresql.ENUM('owner', 'admin', 'editor', 'viewer', name='identity_role', create_type=False)
    role_enum.create(op.get_bind(), checkfirst=True)

    op.create_table(
        'user_tenants',
        sa.Column('membership_id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('role', role_enum, nullable=False),
        sa.Column(
            'scopes', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'[]'::jsonb")
        ),
        sa.Column('plan', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(timezone=False), nullable=False, server_default=func.now()),
        sa.Column(
            'updated_at',
            sa.TIMESTAMP(timezone=False),
            nullable=False,
            server_default=func.now(),
            server_onupdate=func.now(),
        ),
        sa.ForeignKeyConstraint(
            ('user_id',),
            ['identity.users.id'],
            name='fk_user_tenants_user_id_users',
            ondelete='CASCADE',
        ),
        sa.ForeignKeyConstraint(
            ('tenant_id',),
            ['identity.tenants.id'],
            name='fk_user_tenants_tenant_id_tenants',
            ondelete='CASCADE',
        ),
        sa.UniqueConstraint('user_id', 'tenant_id', name='uq_user_tenant_membership'),
        schema='identity',
    )
    op.create_index('ix_identity_user_tenants_user', 'user_tenants', ['user_id'], schema='identity')
    op.create_index('ix_identity_user_tenants_tenant', 'user_tenants', ['tenant_id'], schema='identity')


def downgrade() -> None:
    op.drop_index('ix_identity_user_tenants_tenant', table_name='user_tenants', schema='identity')
    op.drop_index('ix_identity_user_tenants_user', table_name='user_tenants', schema='identity')
    op.drop_table('user_tenants', schema='identity')

    op.drop_index('ix_identity_users_email', table_name='users', schema='identity')
    op.drop_table('users', schema='identity')

    op.drop_table('tenants', schema='identity')

    op.execute('DROP TYPE IF EXISTS identity_role;')
    op.execute('DROP SCHEMA IF EXISTS identity CASCADE;')
