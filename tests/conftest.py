import os
from pathlib import Path

import pytest
from sqlalchemy import text

from alembic import command
from alembic.config import Config
from core.db import get_engine

# Provide default test-friendly configuration values.
# IMPORTANT: Do NOT override POSTGRES_URL here; tests should use a real Postgres for schema support.
os.environ.setdefault('REDIS_URL', 'redis://localhost:6379/0')
os.environ.setdefault('OPENAI_API_KEY', 'test-key')
os.environ.setdefault('TAVILY_API_KEY', 'test-key')
os.environ.setdefault('INTERNAL_AUTH_TOKEN', 'test-token')

# Ensure Alembic knows where to migrate. Default to POSTGRES_URL if ALEMBIC_DATABASE_URL is absent.
if 'ALEMBIC_DATABASE_URL' not in os.environ and 'POSTGRES_URL' in os.environ:
    os.environ['ALEMBIC_DATABASE_URL'] = os.environ['POSTGRES_URL']

# For integration tests, align application DB user with Alembic DB user to avoid privilege issues.
if 'ALEMBIC_DATABASE_URL' in os.environ:
    os.environ['POSTGRES_URL'] = os.environ['ALEMBIC_DATABASE_URL']
    # Reset settings cache so subsequent get_settings() picks up the new env
    try:
        from core.config import get_settings  # local import to avoid early import

        get_settings.cache_clear()  # type: ignore[attr-defined]
        # Also reset any cached engine so new settings take effect
        from sqlmodel import create_engine as sqlmodel_create_engine

        import core.db as core_db  # type: ignore

        # Force the application to use the Alembic (privileged) engine during tests
        core_db._engine = sqlmodel_create_engine(os.environ['ALEMBIC_DATABASE_URL'])  # type: ignore[attr-defined]
    except Exception:
        pass


@pytest.fixture(scope='session')
def anyio_backend():
    return 'asyncio'


@pytest.fixture(scope='session', autouse=True)
def create_database():
    # Run Alembic migrations to set up the schema on Postgres
    alembic_ini = Path(__file__).resolve().parents[1] / 'alembic.ini'
    cfg = Config(str(alembic_ini))
    # Ensure script_location is correct when invoked from tests
    cfg.set_main_option('script_location', str(alembic_ini.parent / 'alembic'))

    command.upgrade(cfg, 'head')

    # After migrating, ensure the test role can access the identity schema & tables.
    # Use the Alembic connection (likely superuser) to grant privileges broadly for tests.
    alembic_url = os.environ.get('ALEMBIC_DATABASE_URL')
    if alembic_url and alembic_url.startswith('postgres'):  # grants only make sense on Postgres
        from sqlalchemy import create_engine as sa_create_engine

        with sa_create_engine(alembic_url).connect() as admin_conn:
            try:
                admin_conn.execute(text('GRANT USAGE ON SCHEMA identity TO PUBLIC'))
                admin_conn.execute(
                    text('GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA identity TO PUBLIC')
                )
                admin_conn.execute(
                    text(
                        'ALTER DEFAULT PRIVILEGES IN SCHEMA identity GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO PUBLIC'
                    )
                )
                admin_conn.commit()
            except Exception:
                admin_conn.rollback()

    try:
        yield
    finally:
        # Drop the identity schema to clean up after tests
        engine = get_engine()
        with engine.connect() as conn:
            try:
                conn.execute(text('DROP SCHEMA IF EXISTS identity CASCADE'))
                conn.commit()
            except Exception:
                # Ignore if we don't have privileges to drop the schema (e.g., shared DB)
                conn.rollback()
