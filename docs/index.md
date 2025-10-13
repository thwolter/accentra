# Accentra Identity Service

Accentra provides tenant-aware user management for multi-tenant SaaS products. The service exposes a FastAPI
application that manages tenants, users, memberships, and access tokens. It is designed to run in a containerised
environment with PostgreSQL for persistence and optional Redis-backed Dramatiq workers for background jobs.

## Architecture at a Glance

- **FastAPI application** (`src/main.py`) wires logging, observability, and the `users` router under `/identity`.
- **Domain modules** (`src/users`) implement SQLModel data structures, Pydantic schemas, authentication helpers, and the
  service layer used by HTTP routes.
- **Shared platform code** (`src/core`) centralises configuration, database sessions, logging, and OpenTelemetry
  integration.
- **Migrations** live in `alembic/` and provision the `identity` schema plus tenant/user tables.
- **Tests** (`tests/unit_tests`, `tests/integration_tests`) exercise API behaviour against a migrated database.

## Domain Concepts

- **Tenant** – logical customer account that owns seats and entitlement (`plan`) data.
- **User** – individual identity with login credentials and profile information.
- **Membership** – join table binding a user to a tenant with a role, scopes, and optional plan overrides.
- **Access token** – signed JWT encoding `sub` (user), `tid` (tenant), `role`, `scopes`, and optional `plan`.

## Request Lifecycle

1. Requests enter FastAPI with logging configured via `src/core/logging.py`.
2. `init_observability()` enables optional OpenTelemetry tracing/metrics exporters when configured.
3. Route handlers resolve a SQLModel `Session` through `core.db.get_session_dependency`.
4. Business logic executes inside `users.service`, committing changes through the session context.
5. Responses serialise SQLModel objects into Pydantic DTOs defined in `users.schemas`.

## When to Use the Service

Use Accentra whenever you need:

- A drop-in identity service with multi-tenancy baked in.
- Consistent JWT access tokens enriched with tenant metadata.
- Safe password handling using PBKDF2 with 390k iterations.
- Schema migrations you can manage through Alembic alongside the application lifecycle.
