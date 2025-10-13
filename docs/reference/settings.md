# Configuration Reference

Application settings are provided through environment variables parsed by `core.config.Settings`. The table below lists
each field, its default value, and usage notes.

| Variable | Default | Notes |
| --- | --- | --- |
| `ENV` | `production` | Controls `deployment.environment` attribute for observability. Accepts `development`, `production`, `testing`. |
| `APP_NAME` | `Accentra` | Used for FastAPI title and OpenTelemetry resource metadata. |
| `DEBUG` | `None` | When `true`, enables SQLAlchemy echo for SQL debugging. |
| `VERSION` | `0.1.0` | Displayed in the FastAPI docs and propagated to OTEL resource attributes. |
| `ADMIN_EMAIL` | `support@riskary.de` | Informational contact value. |
| `POSTGRES_URL` / `DATABASE_URL` / `POSTGRESQL_URL` | _required_ | Database connection string. `pg_vector_url` ensures `postgresql://` prefix. |
| `REDIS_URL` / `REDIS_URI` | _required_ | Redis connection string for Dramatiq broker. |
| `JWT_SECRET_KEY` | `dev-secret-key` | Symmetric secret used for JWT signing. Replace in production. |
| `JWT_ALGORITHM` | `HS256` | Algorithm passed to PyJWT. |
| `JWT_ACCESS_TOKEN_TTL_MINUTES` | `60` | Token lifetime in minutes. |
| `JWT_ISSUER` | `None` | Optional `iss` claim. |
| `JWT_AUDIENCE` | `None` | Optional `aud` claim. Disable audience verification by leaving unset. |
| `LOG_LEVEL` | `INFO` | Global logging level (`DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`). |
| `OTLP_ENDPOINT` | `None` | Base URL for OpenTelemetry OTLP exporters. Enables traces/metrics/logs when set. |
| `OTLP_HEADERS` | `None` | Comma-separated `key=value` pairs forwarded to the OTLP exporters. |
| `OTEL_LOGS_ENABLED` | `False` | Toggle OTLP log forwarding. Requires exporter packages. |
| `OTEL_TRACES_ENABLED` | `True` | Toggle OTLP tracing exporter. |
| `OTEL_METRICS_ENABLED` | `True` | Toggle OTLP metrics exporter. |
| `INTERNAL_AUTH_TOKEN` | `dev-internal-token` | Shared secret for internal probes or service-to-service calls. |

## Additional Environment Variables

The tooling and tests recognise the following auxiliary variables:

- `ALEMBIC_DATABASE_URL` – Explicit connection string for migrations. Falls back to `POSTGRES_URL` when unset.
- `OPENAI_API_KEY` / `TAVILY_API_KEY` – Stubbed in `tests/conftest.py` to satisfy optional integrations. Set when running
  features that depend on third-party services.
- `REDIS_URL`, `POSTGRES_URL` – Seeded with test defaults in `tests/conftest.py` to promote isolated test runs.

Place these values in the project root `.env`. `pydantic-settings` loads them automatically when the application starts.
