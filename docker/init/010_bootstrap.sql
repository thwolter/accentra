-- Create logical roles (no login)
\echo '=== Running bootstrap: creating roles and schema ==='

DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'ddl_owner') THEN
    CREATE ROLE ddl_owner NOLOGIN;
  END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'accentra_rw') THEN
    CREATE ROLE accentra_rw NOLOGIN;
  END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'accentra_ro') THEN
    CREATE ROLE accentra_ro NOLOGIN;
  END IF;
END$$;

-- Create runtime and migration users
DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'accentra_app_user') THEN
    CREATE ROLE accentra_app_user LOGIN PASSWORD 'app-user-password';
  END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'accentra_alembic_user') THEN
    CREATE ROLE accentra_alembic_user LOGIN PASSWORD 'alembic-user-password';
  END IF;
END$$;

-- Memberships
GRANT accentra_rw TO accentra_app_user;
GRANT ddl_owner TO accentra_alembic_user;

-- Dedicated schema owned by ddl_owner
CREATE SCHEMA IF NOT EXISTS identity AUTHORIZATION ddl_owner;

-- Baseline + default privileges so future objects are usable without Alembic issuing GRANTs
GRANT USAGE ON SCHEMA identity TO accentra_rw, accentra_ro;

ALTER DEFAULT PRIVILEGES FOR ROLE accentra_alembic_user IN SCHEMA identity
  GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO accentra_rw;
ALTER DEFAULT PRIVILEGES FOR ROLE accentra_alembic_user IN SCHEMA identity
  GRANT SELECT ON TABLES TO accentra_ro;
ALTER DEFAULT PRIVILEGES FOR ROLE accentra_alembic_user IN SCHEMA identity
  GRANT USAGE, SELECT ON SEQUENCES TO accentra_rw, accentra_ro;
ALTER DEFAULT PRIVILEGES FOR ROLE accentra_alembic_user IN SCHEMA identity
  GRANT EXECUTE ON FUNCTIONS TO accentra_rw, accentra_ro;

-- Optional: enable pgcrypto for gen_random_uuid()
CREATE EXTENSION IF NOT EXISTS pgcrypto;

\echo '=== Bootstrap completed ==='
