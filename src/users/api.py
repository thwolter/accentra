from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlmodel import Session

from core.db import get_session_dependency
from users.models import Membership, Tenant, User
from users.schemas import (
    LoginRequest,
    MembershipCreate,
    MembershipRead,
    TenantCreate,
    TenantRead,
    Token,
    TokenPayload,
    UserCreate,
    UserUpdate,
    UserWithMemberships,
)
from users.security import AuthenticationError, create_access_token, decode_access_token
from users.service import (
    authenticate_user,
    create_membership,
    create_tenant,
    create_user,
    get_membership,
    get_tenant,
    get_user,
    list_memberships,
    update_user,
)

router = APIRouter(prefix='/identity')
bearer_scheme = HTTPBearer(auto_error=False)


def get_session(session: Session = Depends(get_session_dependency)) -> Session:
    return session


def to_tenant_read(tenant: Tenant) -> TenantRead:
    return TenantRead.model_validate(tenant, from_attributes=True)


def to_membership_read(membership: Membership) -> MembershipRead:
    return MembershipRead.model_validate(membership, from_attributes=True)


def serialize_user(session: Session, user: User) -> UserWithMemberships:
    memberships = [to_membership_read(membership) for membership in list_memberships(session, user.id)]
    data = UserWithMemberships.model_validate(user, from_attributes=True)
    return data.model_copy(update={'memberships': memberships})


def get_current_context(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    session: Session = Depends(get_session),
) -> tuple[User, Membership, TokenPayload]:
    if credentials is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Missing bearer token')
    token = credentials.credentials
    try:
        payload = decode_access_token(token)
    except AuthenticationError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc

    user = get_user(session, payload.sub)
    if user is None or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='User not found or inactive')

    membership = get_membership(session, user.id, payload.tid)
    if membership is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='Membership not found for tenant')

    return user, membership, payload


@router.post('/tenants', response_model=TenantRead, status_code=status.HTTP_201_CREATED, tags=['tenants'])
def register_tenant(payload: TenantCreate, session: Session = Depends(get_session)) -> TenantRead:
    tenant = create_tenant(session, payload)
    return to_tenant_read(tenant)


@router.get('/tenants/{tenant_id}', response_model=TenantRead, tags=['tenants'])
def read_tenant(tenant_id: UUID, session: Session = Depends(get_session)) -> TenantRead:
    tenant = get_tenant(session, tenant_id)
    if tenant is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Tenant not found')
    return to_tenant_read(tenant)


@router.post('/users', response_model=UserWithMemberships, status_code=status.HTTP_201_CREATED, tags=['users'])
def register_user(payload: UserCreate, session: Session = Depends(get_session)) -> UserWithMemberships:
    user = create_user(session, payload)
    return serialize_user(session, user)


@router.get('/users/{user_id}', response_model=UserWithMemberships, tags=['users'])
def read_user(user_id: UUID, session: Session = Depends(get_session)) -> UserWithMemberships:
    user = get_user(session, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='User not found')
    return serialize_user(session, user)


@router.patch('/users/{user_id}', response_model=UserWithMemberships, tags=['users'])
def modify_user(user_id: UUID, payload: UserUpdate, session: Session = Depends(get_session)) -> UserWithMemberships:
    user = get_user(session, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='User not found')
    user = update_user(session, user, payload)
    return serialize_user(session, user)


@router.post(
    '/users/{user_id}/memberships',
    response_model=MembershipRead,
    status_code=status.HTTP_201_CREATED,
    tags=['users'],
)
def add_membership(user_id: UUID, payload: MembershipCreate, session: Session = Depends(get_session)) -> MembershipRead:
    membership = create_membership(session, user_id, payload)
    return to_membership_read(membership)


@router.post('/auth/login', response_model=Token, tags=['auth'])
def login(payload: LoginRequest, session: Session = Depends(get_session)) -> Token:
    user, membership = authenticate_user(session, payload)
    token = create_access_token(
        subject=user.id,
        tenant_id=membership.tenant_id,
        role=membership.role,
        scopes=membership.scopes,
        plan=membership.plan,
    )
    return Token(access_token=token)


@router.get('/users/me', response_model=UserWithMemberships, tags=['users'])
def read_current_user(
    context: tuple[User, Membership, TokenPayload] = Depends(get_current_context),
    session: Session = Depends(get_session),
) -> UserWithMemberships:
    user, membership, _ = context
    # Refresh membership to ensure latest data is returned.
    session.refresh(user)
    session.refresh(membership)
    return serialize_user(session, user)
