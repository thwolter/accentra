# Accentra Identity Service

![Pytest](https://img.shields.io/badge/tests-pytest-blue?logo=pytest)
![Ruff Lint](https://img.shields.io/badge/lint-ruff-5A4D8C?logo=ruff)
![Ruff Format](https://img.shields.io/badge/style-ruff%20format-5A4D8C?logo=ruff)
![pre-commit](https://img.shields.io/badge/hooks-pre--commit-FAB040?logo=pre-commit)

Accentra is a FastAPI service that manages tenants, users, and memberships for multi-tenant SaaS applications. It issues
JWT access tokens enriched with tenant context, persists data in PostgreSQL through SQLModel, and exposes optional
observability integrations via OpenTelemetry.

## Highlights

- Multi-tenant data model with per-tenant `plan` metadata.
- Secure credential storage using PBKDF2 (`sha256`, 390k iterations).
- JWT tokens carrying tenant, role, scope, and plan claims.
- Alembic-powered schema migrations targeting the `identity` schema.
- Pluggable observability: logging, tracing, and metrics via OTLP exporters.

## Quick Start

1. **Install dependencies**
   ```bash
   uv sync
   ```
2. **Configure environment** – create `.env` with at least:
   ```ini
   POSTGRES_URL=postgresql://accentra:accentra@localhost:5432/accentra
   REDIS_URL=redis://localhost:6379/0
   JWT_SECRET_KEY=change-me
   ```
3. **Apply migrations**
   ```bash
   uv run alembic upgrade head
   ```
4. **Run the API**
   ```bash
   uv run uvicorn src.main:app --reload
   ```
   Health endpoints live at `/healthz` and `/readyz`; the identity routes mount under `/identity`.

## Tests and Quality Gates

Run the same checks enforced by the pre-commit configuration:

```bash
uv run pytest
uv run ruff check .
uv run ruff format .
uv run pre-commit run --all-files
```

## Project Layout

```
src/
  main.py            # FastAPI entry point wiring routers and observability
  core/              # Configuration, database engine, logging, OTEL helpers, Dramatiq broker
  users/             # SQLModel models, Pydantic schemas, service layer, API router
alembic/             # Migration environment and versioned scripts
docs/                # MkDocs documentation
tests/               # Unit and integration suites (pytest)
```

## Configuration

Settings load from environment variables via `pydantic-settings`. Review `docs/reference/settings.md` for defaults and
override options. The service expects at minimum `POSTGRES_URL` and `REDIS_URL`; JWT settings default to development
values and must be rotated in production.

## Documentation

Serve the MkDocs site locally:

```bash
uv run mkdocs serve
```

Build static documentation into `site/`:

```bash
uv run mkdocs build
```

Key guides:
- Overview and architecture: `docs/index.md`
- Setup instructions: `docs/getting-started.md`
- API usage: `docs/api/identity.md`
- Operations playbook: `docs/operations.md`

## Contributing

1. Install git hooks locally:
   ```bash
   uv run pre-commit install
   ```
2. Make changes in a feature branch and run the quality gates listed above.
3. Follow Conventional Commits (enforced with Commitizen via `uv run cz commit`).

## Security

- JWT-protected routes expect `Authorization: Bearer <token>` headers. Tokens must contain `tid` (tenant) and `sub`
  (user) claims.
- Keep secrets out of version control; `.env` values load automatically through `pydantic-settings`.
- Use the `internal_auth_token` only for trusted internal probes and rotate it before promotion to production.

## License

Licensed under the MIT License. See `pyproject.toml` for details.
