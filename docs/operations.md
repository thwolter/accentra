# Operations

This section covers day-two activities for running Accentra in staging or production environments.

## Health Probes

- `GET /healthz` returns `{"status": "ok"}` and should be used for liveness checks.
- `GET /readyz` returns `{"status": "ready"}` and should be paired with dependency verification (database, brokers).

Both endpoints are anonymous and fast, making them suitable for Kubernetes-style probes.

## Logging

`core.logging.configure_logging()` initialises stdlib logging with a structured format:

```
2024-12-10 09:32:17 INFO [uvicorn.access] 127.0.0.1:63328 - "GET /identity/users/me HTTP/1.1" 200
```

Configuration notes:

- Default log level is `INFO`, sourced from `Settings.log_level`.
- When `otel_logs_enabled` is `true` and `otlp_endpoint` is provided, logs are forwarded to the OTLP collector via the
  HTTP exporter (requires optional OpenTelemetry packages).

## Observability

`core.observability.init_observability()` prepares OpenTelemetry tracing and metrics:

- Controlled by `otel_traces_enabled` and `otel_metrics_enabled`.
- Requires `opentelemetry-sdk` and relevant OTLP exporters (`opentelemetry-exporter-otlp`).
- Uses service attributes `service.name`, `service.version`, and `deployment.environment`.

Ensure the environment sets:

```bash
OTLP_ENDPOINT=https://otel-collector.example.com/v1/traces
OTLP_HEADERS=Authorization=Bearer%20token,Other=Value
```

Headers are comma separated `key=value` pairs. Missing or malformed pairs are ignored.

## Database Management

- SQLModel models reside in `users.models` and target the `identity` schema.
- Migrations are managed by Alembic. Run `uv run alembic upgrade head` to reach the newest revision.
- During tests, fixtures in `tests/conftest.py` migrate the schema and drop it afterwards. Grant privileges if you run
  the suite against a shared cluster.
- `core.db.session_scope()` safely applies tenant context to PostgreSQL connections by setting session-local GUCs
  `app.tenant_id` and `app.user_id`.

### Engine Selection

- `POSTGRES_URL` / `DATABASE_URL` / `POSTGRESQL_URL` environment variables configure the runtime engine.
- For local experimentation you can point the service at SQLite; in-memory mode automatically activates a `StaticPool`.

## Queueing

`core.queueing` exposes a Redis-backed Dramatiq broker:

- `core.queueing.setup_broker()` reconfigures the global broker (used by CLI invocations).
- Ensure `REDIS_URL` is provided; otherwise, the process exits with `RuntimeError`.
- When deploying, start workers with `dramatiq --broker core.queueing:broker` so that the central broker configuration
  is reused.

## Security Considerations

- Do not rely on application-level enforcement to protect provisioning routes; add an API gateway or adjust the FastAPI
  dependencies to require authentication for tenant and user management.
- Access tokens use symmetric signing (`HS256`). Rotate `jwt_secret_key` through standard secret management practices.
- PBKDF2 parameters are defined in `users.security.PBKDF_ITERATIONS`. Consider reviewing iteration counts periodically
  to keep pace with hardware advances.

## Backups and Disaster Recovery

- Take regular PostgreSQL snapshots that include the `identity` schema.
- If Redis queues store critical jobs, ensure persistence via AOF or external backpressure mechanisms.

## Deployment Checklist

- [ ] Populate `.env` with production secrets and URLs.
- [ ] Run `uv run alembic upgrade head`.
- [ ] Confirm `uv run pytest -q` passes in the build pipeline.
- [ ] Configure OTLP exporters or disable them explicitly to avoid startup warnings.
- [ ] Set up a cron or job to rotate and prune expired JWT secrets if you migrate to asymmetric keys.
