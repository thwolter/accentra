from __future__ import annotations

from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest

from users.models import Role
from users.security import (
    AuthenticationError,
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)


def test_hash_password_roundtrip() -> None:
    password = 'Sup3r-Secret!'
    encoded = hash_password(password)

    assert encoded != password
    assert verify_password(password, encoded)
    assert not verify_password('wrong-password', encoded)


def test_create_and_decode_access_token() -> None:
    now = datetime(2024, 1, 1, tzinfo=timezone.utc)
    user_id = uuid4()
    tenant_id = uuid4()
    token = create_access_token(
        subject=user_id,
        tenant_id=tenant_id,
        role=Role.admin,
        scopes=['users:read', 'users:write'],
        plan={'tier': 'pro'},
        issued_at=now,
        expires_delta=timedelta(minutes=30),
    )

    payload = decode_access_token(token)

    assert payload.sub == user_id
    assert payload.tid == tenant_id
    assert payload.role is Role.admin
    assert payload.scopes == ['users:read', 'users:write']
    assert payload.plan == {'tier': 'pro'}
    assert payload.iat == int(now.timestamp())
    assert payload.exp == int((now + timedelta(minutes=30)).timestamp())


def test_decode_access_token_rejects_invalid_token() -> None:
    with pytest.raises(AuthenticationError):
        decode_access_token('not-a-real-token')
