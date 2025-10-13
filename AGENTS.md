# Repository Guidelines

## Project Structure & Module Organization
The FastAPI entry point lives in `src/main.py`, where `create_app()` wires logging, observability, and routers. Domain logic is grouped under `src/metadata/` (API, models, tasks), shared platform code resides in `src/core/` (config, database, observability, queueing), and helpers sit in `src/utils/` and `src/agent/`. Database migrations are kept in `alembic/` with version scripts under `alembic/versions/`. Tests live in `tests/`, separated into `unit_tests/`, `integration_tests/`, and service-level checks such as `test_metadata_service.py`. MkDocs content is maintained in `docs/`.

## Build, Test, and Development Commands
Install or refresh dependencies with `uv sync`. Start the API locally using `uv run uvicorn src.main:app --reload`. Apply migrations via `uv run alembic upgrade head`. Run quality gates through `uv run pytest` (tests), `uv run ruff check .` (lint), `uv run ruff format .` (formatter), and `uv run pre-commit run --all-files` to mirror the CI hook set. Serve docs with `uv run mkdocs serve` or build static assets with `uv run mkdocs build`.

## Coding Style & Naming Conventions
Target Python 3.12, four-space indentation, and a 120-character line limit enforced by Ruff. Prefer single quotes for strings and explicit type hints on public interfaces. Modules, packages, and tests stay snake_case; FastAPI routes use lowercase-with-dashes paths. Keep imports sorted through `isort`/`ssort`, and run Ruff formatting before committing.

## Testing Guidelines
Use Pytest across the suite; name files `test_*.py` and mark async cases with `@pytest.mark.asyncio`. Unit tests should isolate services within `tests/unit_tests/`, while integration tests exercise database and queue interactions under `tests/integration_tests/` using fixtures defined in `tests/conftest.py`. Add regression coverage for new endpoints, migrations, and background tasks, and ensure `uv run pytest -q` completes cleanly before opening a PR. Configure `LANGSMITH_API_KEY` when running tests that depend on LangSmith.

## Commit & Pull Request Guidelines
Follow Conventional Commit syntax (`type(scope): subject`)—the repository is configured with Commitizen, so prefer `uv run cz commit` for guided messages. Squash work into logical commits, reference issue links in the body, and call out migrations or configuration changes explicitly. Pull requests should summarize the change, list verification steps, and include any documentation updates or screenshots reviewers need.

## Security & Configuration Tips
Metadata routes enforce `Authorization: Bearer <jwt>` headers; local tokens must include `tid` and `sub` claims. Secrets load from `.env` through `pydantic-settings`—provide values for `postgres_url`, `redis_url`, `openai_api_key`, and optional OTLP endpoints, but never commit them. Use the `internal_auth_token` only for development probes, and rotate tokens before promoting to production.
