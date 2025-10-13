from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import JSON, Boolean, Column, DateTime
from sqlalchemy import Enum as SqlEnum
from sqlalchemy import String, UniqueConstraint, func, text
from sqlmodel import Field, SQLModel

IDENTITY_SCHEMA = 'identity'

__all__ = ['IDENTITY_SCHEMA', 'Role', 'Tenant', 'User', 'Membership']


class Role(str, Enum):
    owner = 'owner'
    admin = 'admin'
    editor = 'editor'
    viewer = 'viewer'


class Tenant(SQLModel, table=True):
    __tablename__ = 'tenants'  # type: ignore[bad-override]
    __table_args__ = {'schema': IDENTITY_SCHEMA}

    id: UUID = Field(default_factory=uuid4, primary_key=True, index=True)
    name: str = Field(sa_column=Column(String(length=255), nullable=False, unique=True))
    plan: Any | None = Field(
        default=None,
        sa_column=Column(JSON, nullable=True),
        description='Serialized plan/entitlement payload.',
    )
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(DateTime(timezone=False), nullable=False, server_default=func.now()),
    )
    updated_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(
            DateTime(timezone=False),
            nullable=False,
            server_default=func.now(),
            server_onupdate=func.now(),
        ),
    )


class User(SQLModel, table=True):
    __tablename__ = 'users'  # type: ignore[bad-override]
    __table_args__ = {'schema': IDENTITY_SCHEMA}

    id: UUID = Field(default_factory=uuid4, primary_key=True, index=True)
    email: str = Field(sa_column=Column(String(length=255), nullable=False, unique=True, index=True))
    full_name: str | None = Field(default=None, sa_column=Column(String(length=255), nullable=True))
    hashed_password: str = Field(sa_column=Column(String(length=512), nullable=False))
    is_active: bool = Field(
        default=True,
        sa_column=Column(Boolean, nullable=False, server_default=text('TRUE')),
    )
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(DateTime(timezone=False), nullable=False, server_default=func.now()),
    )
    updated_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(
            DateTime(timezone=False),
            nullable=False,
            server_default=func.now(),
            server_onupdate=func.now(),
        ),
    )


class Membership(SQLModel, table=True):
    __tablename__ = 'user_tenants'  # type: ignore[bad-override]
    __table_args__ = (
        UniqueConstraint('user_id', 'tenant_id', name='uq_user_tenant_membership'),
        {'schema': IDENTITY_SCHEMA},
    )

    membership_id: UUID = Field(default_factory=uuid4, primary_key=True, index=True)
    user_id: UUID = Field(foreign_key=f'{IDENTITY_SCHEMA}.users.id', nullable=False)
    tenant_id: UUID = Field(foreign_key=f'{IDENTITY_SCHEMA}.tenants.id', nullable=False)
    role: Role = Field(
        sa_column=Column(SqlEnum(Role, name='identity_role', create_constraint=True), nullable=False),
    )
    scopes: list[str] = Field(
        default_factory=list,
        sa_column=Column(JSON, nullable=False, default=list),
    )
    plan: Any | None = Field(
        default=None,
        sa_column=Column(JSON, nullable=True),
    )
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(DateTime(timezone=False), nullable=False, server_default=func.now()),
    )
    updated_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(
            DateTime(timezone=False),
            nullable=False,
            server_default=func.now(),
            server_onupdate=func.now(),
        ),
    )
