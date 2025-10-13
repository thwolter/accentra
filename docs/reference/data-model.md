# Data Model

Accentra persists identity data in the PostgreSQL `identity` schema using SQLModel. The schema is managed by Alembic
migrations and comprises tenants, users, and memberships.

## Tenants

- **Table:** `identity.tenants`
- **Primary key:** `id` (`UUID`)
- **Unique constraints:** `name`
- **Columns:**
  - `name` – required tenant name (`VARCHAR(255)`).
  - `plan` – JSON payload describing the commercial plan or entitlements.
  - `created_at`, `updated_at` – UTC timestamps (`TIMESTAMP WITHOUT TIME ZONE`) with server defaults.

Tenants can store arbitrary `plan` metadata, allowing downstream services to tailor behaviour based on entitlements.

## Users

- **Table:** `identity.users`
- **Primary key:** `id` (`UUID`)
- **Unique constraints:** `email`
- **Columns:**
  - `email` – login identifier (`VARCHAR(255)`) validated via `EmailStr`.
  - `full_name` – optional display name.
  - `hashed_password` – salted PBKDF2 digest (`SHA-256`, `390000` iterations).
  - `is_active` – Boolean flag defaulting to `TRUE`.
  - `created_at`, `updated_at` – UTC timestamps with server defaults.

Passwords are stored as `<salt_hex>$<digest_hex>` and verified with `users.security.verify_password`.

## Memberships

- **Table:** `identity.user_tenants`
- **Primary key:** `membership_id` (`UUID`)
- **Unique constraints:** `uq_user_tenant_membership` on (`user_id`, `tenant_id`)
- **Columns:**
  - `user_id` – foreign key to `identity.users.id`.
  - `tenant_id` – foreign key to `identity.tenants.id`.
  - `role` – enum (`owner`, `admin`, `editor`, `viewer`).
  - `scopes` – JSON array of strings describing fine-grained permissions.
  - `plan` – optional JSON override applied to the user's membership.
  - `created_at`, `updated_at` – UTC timestamps with server defaults.

Roles encode coarse-grained access levels, while scopes enable feature flags or granular permissions. Membership payloads
also carry `plan` overrides to support seat upgrades or beta features for specific members.

## Access Context

`core.db.session_scope()` can attach a tenant-aware access context to each SQL session. When connected to PostgreSQL, the
function sets GUCs (`app.tenant_id`, `app.user_id`) that downstream triggers or policies can consume. The session also
stores the identifiers in `session.info` for application-level logic.
