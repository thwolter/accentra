"""Create application DB role and grant privileges on identity schema."""

from __future__ import annotations

import os

from sqlalchemy import text

from alembic import op

# Revision identifiers, used by Alembic.
revision = '0003_create_app_role'
down_revision = '0002_identity_user_management'
branch_labels = None
depends_on = None


def _get_role_name() -> str:
    # Allow configuring the role name via env; provide sane default
    return os.getenv('APP_DB_ROLE', 'accentra_app_role')


def upgrade() -> None:
    bind = op.get_bind()

    role_name = _get_role_name()

    # Determine current database name for GRANT CONNECT
    db_name = bind.execute(text('SELECT current_database()')).scalar()  # type: ignore[assignment]

    # Create role if it doesn't exist and allow LOGIN (password-less here; operator can ALTER as needed)
    bind.execute(
        text(
            """
            DO $$
            BEGIN
                IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = :role_name) THEN
                    EXECUTE 'CREATE ROLE ' || quote_ident(:role_name);
                END IF;
            END$$;
            """
        ),
        {'role_name': role_name},
    )

    # Grant basic connectivity and schema/table privileges for our service usage
    # Note: USAGE on schema and DML on tables; sequences granted for future proofing
    if isinstance(db_name, str) and db_name:
        bind.execute(text(f'GRANT CONNECT ON DATABASE "{db_name}" TO "{role_name}"'))

    # Ensure schema exists (should already be created by previous migration/env.py)
    bind.execute(text('CREATE SCHEMA IF NOT EXISTS identity'))

    bind.execute(text(f'GRANT USAGE ON SCHEMA identity TO "{role_name}"'))
    bind.execute(text(f'GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA identity TO "{role_name}"'))
    bind.execute(text(f'GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA identity TO "{role_name}"'))

    # Default privileges for future tables and sequences created in this schema
    bind.execute(
        text(
            f'ALTER DEFAULT PRIVILEGES IN SCHEMA identity GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO "{role_name}"'
        )
    )
    bind.execute(text(f'ALTER DEFAULT PRIVILEGES IN SCHEMA identity GRANT USAGE, SELECT ON SEQUENCES TO "{role_name}"'))


def downgrade() -> None:
    bind = op.get_bind()
    role_name = _get_role_name()

    # Revoke privileges (idempotent-ish; ignore if not present)
    for stmt in [
        f'REVOKE USAGE ON SCHEMA identity FROM "{role_name}"',
        f'REVOKE SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA identity FROM "{role_name}"',
        f'REVOKE USAGE, SELECT ON ALL SEQUENCES IN SCHEMA identity FROM "{role_name}"',
        f'ALTER DEFAULT PRIVILEGES IN SCHEMA identity REVOKE SELECT, INSERT, UPDATE, DELETE ON TABLES FROM "{role_name}"',
        f'ALTER DEFAULT PRIVILEGES IN SCHEMA identity REVOKE USAGE, SELECT ON SEQUENCES FROM "{role_name}"',
    ]:
        try:
            bind.execute(text(stmt))
        except Exception:
            # Best-effort in downgrade
            pass

    # Revoke database-level privileges to allow role drop
    db_name = bind.execute(text('SELECT current_database()')).scalar()
    if isinstance(db_name, str) and db_name:
        try:
            bind.execute(text(f'REVOKE CONNECT ON DATABASE "{db_name}" FROM "{role_name}"'))
            bind.execute(text(f'REVOKE ALL PRIVILEGES ON DATABASE "{db_name}" FROM "{role_name}"'))
        except Exception:
            # Best-effort cleanup
            pass

    # Drop role if exists
    bind.execute(
        text(
            """
            DO $$
            BEGIN
                IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = :role_name) THEN
                    EXECUTE 'DROP ROLE ' || quote_ident(:role_name);
                END IF;
            END$$;
            """
        ),
        {'role_name': role_name},
    )
