from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field

from users.models import Role

PlanData = str | dict[str, Any] | None


class TenantBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    plan: PlanData = None


class TenantCreate(TenantBase):
    pass


class TenantRead(TenantBase):
    id: UUID
    created_at: datetime
    updated_at: datetime


class UserBase(BaseModel):
    email: EmailStr
    full_name: str | None = Field(default=None, max_length=255)
    is_active: bool = True


class UserCreate(UserBase):
    password: str = Field(..., min_length=8, max_length=256)


class UserRead(UserBase):
    id: UUID
    created_at: datetime
    updated_at: datetime


class UserUpdate(BaseModel):
    full_name: str | None = Field(default=None, max_length=255)
    password: str | None = Field(default=None, min_length=8, max_length=256)
    is_active: bool | None = None


class MembershipBase(BaseModel):
    tenant_id: UUID
    role: Role
    scopes: list[str] = Field(default_factory=list)
    plan: PlanData = None


class MembershipCreate(MembershipBase):
    pass


class MembershipRead(MembershipBase):
    membership_id: UUID
    created_at: datetime
    updated_at: datetime


class UserWithMemberships(UserRead):
    memberships: list[MembershipRead] = Field(default_factory=list)


class LoginRequest(BaseModel):
    email: EmailStr
    # Accept any non-empty password to allow proper 401 responses for bad credentials
    password: str
    tenant_id: UUID


class Token(BaseModel):
    access_token: str
    token_type: str = 'bearer'


class TokenPayload(BaseModel):
    sub: UUID
    tid: UUID
    role: Role
    scopes: list[str]
    plan: PlanData = None
    iat: int
    exp: int
    iss: str | None = None
    aud: str | None = None
