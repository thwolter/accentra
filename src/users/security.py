from __future__ import annotations

import hashlib
import hmac
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import UUID

import jwt
from jwt import ExpiredSignatureError, InvalidTokenError

from core.config import get_settings
from users.models import Role
from users.schemas import PlanData, TokenPayload

PBKDF_ITERATIONS = 390000


class AuthenticationError(Exception):
    """Raised when token verification or password checks fail."""


def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    derived = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), bytes.fromhex(salt), PBKDF_ITERATIONS)
    return f'{salt}${derived.hex()}'


def verify_password(password: str, encoded: str) -> bool:
    try:
        salt_hex, digest_hex = encoded.split('$', 1)
    except ValueError:
        return False
    derived = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), bytes.fromhex(salt_hex), PBKDF_ITERATIONS)
    return hmac.compare_digest(digest_hex, derived.hex())


def create_access_token(
    *,
    subject: UUID,
    tenant_id: UUID,
    role: Role,
    scopes: list[str],
    plan: PlanData = None,
    expires_delta: timedelta | None = None,
    issued_at: datetime | None = None,
) -> str:
    settings = get_settings()
    issued_at = issued_at or datetime.now(timezone.utc)
    expires_delta = expires_delta or timedelta(minutes=settings.jwt_access_token_ttl_minutes)
    expire = issued_at + expires_delta

    payload: dict[str, Any] = {
        'sub': str(subject),
        'tid': str(tenant_id),
        'role': role.value,
        'scopes': scopes,
        'iat': int(issued_at.timestamp()),
        'exp': int(expire.timestamp()),
    }
    if plan is not None:
        payload['plan'] = plan
    if settings.jwt_issuer:
        payload['iss'] = settings.jwt_issuer
    if settings.jwt_audience:
        payload['aud'] = settings.jwt_audience

    token = jwt.encode(payload, settings.jwt_secret_key.get_secret_value(), algorithm=settings.jwt_algorithm)
    return token


def decode_access_token(token: str) -> TokenPayload:
    settings = get_settings()
    options: dict[str, Any] = {}
    audience: str | None = None
    if settings.jwt_audience:
        audience = settings.jwt_audience
    else:
        options['verify_aud'] = False

    try:
        decoded = jwt.decode(
            token,
            settings.jwt_secret_key.get_secret_value(),
            algorithms=[settings.jwt_algorithm],
            audience=audience,
            options=options,
        )
    except ExpiredSignatureError as exc:
        raise AuthenticationError('Token has expired') from exc
    except InvalidTokenError as exc:
        raise AuthenticationError('Token is invalid') from exc

    return TokenPayload(
        sub=UUID(decoded['sub']),
        tid=UUID(decoded['tid']),
        role=Role(decoded['role']),
        scopes=list(decoded.get('scopes', [])),
        plan=decoded.get('plan'),
        iat=int(decoded['iat']),
        exp=int(decoded['exp']),
        iss=decoded.get('iss'),
        aud=decoded.get('aud'),
    )
