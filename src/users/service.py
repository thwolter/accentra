from __future__ import annotations

from uuid import UUID

from fastapi import HTTPException, status
from sqlmodel import Session, select

from users.models import Membership, Tenant, User
from users.schemas import (
    LoginRequest,
    MembershipCreate,
    TenantCreate,
    UserCreate,
    UserUpdate,
)
from users.security import hash_password, verify_password


def get_user(session: Session, user_id: UUID) -> User | None:
    return session.get(User, user_id)


def get_user_by_email(session: Session, email: str) -> User | None:
    return session.exec(select(User).where(User.email == email)).first()


def create_user(session: Session, payload: UserCreate) -> User:
    if get_user_by_email(session, payload.email):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail='User already exists')
    user = User(
        email=payload.email,
        full_name=payload.full_name,
        hashed_password=hash_password(payload.password),
        is_active=payload.is_active,
    )
    session.add(user)
    session.flush()
    session.refresh(user)
    return user


def update_user(session: Session, user: User, payload: UserUpdate) -> User:
    if payload.full_name is not None:
        user.full_name = payload.full_name
    if payload.is_active is not None:
        user.is_active = payload.is_active
    if payload.password:
        user.hashed_password = hash_password(payload.password)
    session.add(user)
    session.flush()
    session.refresh(user)
    return user


def create_tenant(session: Session, payload: TenantCreate) -> Tenant:
    if session.exec(select(Tenant).where(Tenant.name == payload.name)).first():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail='Tenant already exists')
    tenant = Tenant(name=payload.name, plan=payload.plan)
    session.add(tenant)
    session.flush()
    session.refresh(tenant)
    return tenant


def get_tenant(session: Session, tenant_id: UUID) -> Tenant | None:
    return session.get(Tenant, tenant_id)


def get_membership(session: Session, user_id: UUID, tenant_id: UUID) -> Membership | None:
    statement = select(Membership).where(Membership.user_id == user_id, Membership.tenant_id == tenant_id)
    return session.exec(statement).first()


def create_membership(session: Session, user_id: UUID, payload: MembershipCreate) -> Membership:
    if not get_user(session, user_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='User not found')
    if not get_tenant(session, payload.tenant_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Tenant not found')
    if get_membership(session, user_id, payload.tenant_id):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail='Membership already exists')

    membership = Membership(
        user_id=user_id,
        tenant_id=payload.tenant_id,
        role=payload.role,
        scopes=list(payload.scopes),
        plan=payload.plan,
    )
    session.add(membership)
    session.flush()
    session.refresh(membership)
    return membership


def list_memberships(session: Session, user_id: UUID) -> list[Membership]:
    statement = select(Membership).where(Membership.user_id == user_id)
    return list(session.exec(statement).all())


def authenticate_user(session: Session, payload: LoginRequest) -> tuple[User, Membership]:
    user = get_user_by_email(session, payload.email)
    if user is None or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Invalid credentials')
    if not verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Invalid credentials')

    membership = get_membership(session, user.id, payload.tenant_id)
    if membership is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='User not assigned to tenant')

    return user, membership
