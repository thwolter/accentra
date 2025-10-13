from __future__ import annotations

from typing import Generator
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from main import create_app


@pytest.fixture()
def client() -> Generator[TestClient, None, None]:
    app = create_app()
    with TestClient(app) as test_client:
        yield test_client


def test_user_management_flow(client: TestClient) -> None:
    tenant_payload = {'name': f'Acme-{uuid4()}', 'plan': {'tier': 'enterprise'}}
    tenant_resp = client.post('/identity/tenants', json=tenant_payload)
    assert tenant_resp.status_code == 201
    tenant_body = tenant_resp.json()
    tenant_id = tenant_body['id']
    assert tenant_body['plan'] == tenant_payload['plan']

    user_payload = {
        'email': f'owner+{uuid4()}@example.com',
        'full_name': 'Owner User',
        'password': 'StrongPassw0rd!',
        'is_active': True,
    }
    user_resp = client.post('/identity/users', json=user_payload)
    assert user_resp.status_code == 201, user_resp.text
    user_body = user_resp.json()
    user_id = user_body['id']
    assert user_body['email'] == user_payload['email']
    assert user_body['memberships'] == []

    membership_payload = {
        'tenant_id': tenant_id,
        'role': 'owner',
        'scopes': ['users:manage'],
        'plan': {'tier': 'enterprise', 'seats': 10},
    }
    membership_resp = client.post(f'/identity/users/{user_id}/memberships', json=membership_payload)
    assert membership_resp.status_code == 201, membership_resp.text
    membership_body = membership_resp.json()
    assert membership_body['role'] == 'owner'
    assert membership_body['scopes'] == ['users:manage']
    assert membership_body['plan'] == membership_payload['plan']

    login_payload = {
        'email': user_payload['email'],
        'password': user_payload['password'],
        'tenant_id': tenant_id,
    }
    login_resp = client.post('/identity/auth/login', json=login_payload)
    assert login_resp.status_code == 200, login_resp.text
    token_body = login_resp.json()
    assert token_body['token_type'] == 'bearer'
    token = token_body['access_token']

    me_resp = client.get('/identity/users/me', headers={'Authorization': f'Bearer {token}'})
    assert me_resp.status_code == 200, me_resp.text
    me_body = me_resp.json()
    assert me_body['email'] == user_payload['email']
    assert me_body['memberships'][0]['tenant_id'] == tenant_id
    assert me_body['memberships'][0]['role'] == 'owner'


def test_login_rejects_invalid_credentials(client: TestClient) -> None:
    tenant_resp = client.post('/identity/tenants', json={'name': f'Widget-{uuid4()}'})
    assert tenant_resp.status_code == 201
    tenant_id = tenant_resp.json()['id']

    user_resp = client.post(
        '/identity/users',
        json={
            'email': f'user+{uuid4()}@example.com',
            'full_name': 'Normal User',
            'password': 'ValidPass123!',
        },
    )
    assert user_resp.status_code == 201
    user_id = user_resp.json()['id']

    client.post(
        f'/identity/users/{user_id}/memberships',
        json={'tenant_id': tenant_id, 'role': 'viewer', 'scopes': []},
    )

    bad_login = client.post(
        '/identity/auth/login',
        json={'email': user_resp.json()['email'], 'password': 'wrong', 'tenant_id': tenant_id},
    )
    assert bad_login.status_code == 401

    bad_membership = client.post(
        '/identity/auth/login',
        json={'email': user_resp.json()['email'], 'password': 'ValidPass123!', 'tenant_id': str(uuid4())},
    )
    assert bad_membership.status_code == 403
