# Getting Started

This guide walks through setting up a development environment, running the API, and executing the test suite.

## Prerequisites

- Python 3.12
- [uv](https://docs.astral.sh/uv/) for dependency and virtual-environment management
- PostgreSQL 15+ with a database created for the identity schema
- Redis (optional, required for Dramatiq workers)

## Install Dependencies

```bash
uv sync
```

The command creates a virtual environment (if absent) and installs both runtime and development dependencies listed in
`pyproject.toml`.

## Configure Environment Variables

Duplicate the provided `.env.example` (if present) or create a `.env` at the repository root with the following minimum
settings:

```bash
POSTGRES_URL=postgresql://accentra:accentra@localhost:5432/accentra
REDIS_URL=redis://localhost:6379/0
JWT_SECRET_KEY=change-me
```

See `reference/settings.md` for the complete list of tunables and their defaults.

## Apply Database Migrations

```bash
uv run alembic upgrade head
```

The Alembic environment expects `ALEMBIC_DATABASE_URL`. If it is not provided, the command falls back to `POSTGRES_URL`.
Migrations create the `identity` schema plus tenant, user, and membership tables.

## Run the API Locally

```bash
uv run uvicorn src.main:app --reload
```

The server listens on `http://127.0.0.1:8000`. Health endpoints are available at `/healthz` and `/readyz`. Mount the
OpenAPI docs at `/docs` once authentication is configured.

## Execute Tests and Quality Gates

```bash
uv run pytest
uv run ruff check .
uv run ruff format .
uv run pre-commit run --all-files
```

Integration tests expect a migrated PostgreSQL instance. Fixtures in `tests/conftest.py` will migrate and later drop the
schema automatically when pointed at a dedicated test database.

## Optional: Launch Dramatiq Workers

If you add Dramatiq actors to the project, point them at the shared Redis broker declared in `core.queueing`. Once the
broker is configured, start workers with:

```bash
uv run dramatiq path.to.module --processes 1 --threads 4 --broker core.queueing:broker
```

Replace `path.to.module` with the module that imports your actors so Dramatiq registers them on startup.
