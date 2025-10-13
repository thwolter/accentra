# Identity API

All routes are mounted under `/identity`. Unless stated otherwise, responses follow FastAPI's default JSON encoding and
error structure (`{"detail": "..."}`).

## Auth Tokens

- JWT bearer tokens are created via `POST /identity/auth/login`.
- The token payload includes `sub` (user id), `tid` (tenant id), `role`, `scopes`, `plan` (optional), `iat`, and `exp`.
- Only the `GET /identity/users/me` endpoint currently enforces authentication. Other routes should be protected by an
  API gateway or future policy to avoid anonymous provisioning.

Typical `Authorization` header:

```http
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

## Tenants

### Create tenant

- **Method & path:** `POST /identity/tenants`
- **Request body:**

```json
{
  "name": "Acme",
  "plan": {
    "tier": "pro",
    "seats": 50
  }
}
```

- **Success response:** `201 Created` with the tenant document (UUIDs and timestamps populated).
- **Errors:** `409 Conflict` when a tenant with the same name already exists.

### Retrieve tenant

- **Method & path:** `GET /identity/tenants/{tenant_id}`
- **Auth:** none
- **Success response:** `200 OK` with the tenant resource.
- **Errors:** `404 Not Found` when the tenant id is unknown.

## Users

### Create user

- **Method & path:** `POST /identity/users`
- **Request body:**

```json
{
  "email": "user@example.com",
  "full_name": "Ada Lovelace",
  "password": "s3cur3P@ss",
  "is_active": true
}
```

- **Behaviour:** Passwords are hashed with PBKDF2 (`sha256`, 390k iterations) before storage.
- **Success response:** `201 Created` with the user document (defaults applied) and an empty `memberships` array.
- **Errors:** `409 Conflict` when the email is already registered.

### Retrieve current user

- **Method & path:** `GET /identity/users/me`
- **Auth:** bearer token required; uses the membership encoded in the JWT to look up role and scopes.
- **Success response:** `200 OK` with the user profile and memberships refreshed from the database.
- **Errors:** `401 Unauthorized` when the token is missing/invalid or the user is inactive. `403 Forbidden` when no
  membership exists for the tenant in the token.

### Retrieve user by id

- **Method & path:** `GET /identity/users/{user_id}`
- **Auth:** none by default (protect externally if needed).
- **Success response:** `200 OK` with the user profile and memberships.
- **Errors:** `404 Not Found` when the user id is unknown.

### Update user

- **Method & path:** `PATCH /identity/users/{user_id}`
- **Body fields:** any subset of `full_name`, `password`, and `is_active`. Omitting a field leaves it unchanged.
- **Success response:** `200 OK` with the updated profile.
- **Errors:** `404 Not Found` when the user id is unknown.

## Memberships

### Add membership

- **Method & path:** `POST /identity/users/{user_id}/memberships`
- **Request body:**

```json
{
  "tenant_id": "1b36bcfa-5ab0-4dd1-8f2c-5b86debe92e1",
  "role": "admin",
  "scopes": ["billing:read", "users:write"],
  "plan": null
}
```

- **Success response:** `201 Created` with the membership record.
- **Errors:** `404 Not Found` when the user or tenant does not exist; `409 Conflict` when the membership already exists.

### List memberships

Memberships are embedded in user responses. Use `GET /identity/users/{user_id}` or `.../users/me` to retrieve them.

## Authentication

### Login

- **Method & path:** `POST /identity/auth/login`
- **Request body:**

```json
{
  "email": "user@example.com",
  "password": "s3cur3P@ss",
  "tenant_id": "1b36bcfa-5ab0-4dd1-8f2c-5b86debe92e1"
}
```

- **Success response:** `200 OK` with `{ "access_token": "<jwt>", "token_type": "bearer" }`.
- **Errors:**
  - `401 Unauthorized` when the credentials are incorrect or the user is inactive.
  - `403 Forbidden` when the user lacks membership for the supplied tenant.

### Token payload example

```json
{
  "sub": "f3c258fc-03b5-4a3d-86e6-6aa7d8acd053",
  "tid": "1b36bcfa-5ab0-4dd1-8f2c-5b86debe92e1",
  "role": "owner",
  "scopes": ["*"],
  "plan": {
    "tier": "enterprise"
  },
  "iat": 1733874840,
  "exp": 1733878440,
  "iss": "accentra",
  "aud": "accentra-clients"
}
```
