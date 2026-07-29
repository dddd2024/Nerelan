#!/bin/sh
set -eu

case "${LITELLM_DATABASE_PASSWORD:-}" in
  ""|*[!A-Za-z0-9_-]*) exit 1 ;;
esac

export PGPASSWORD="${POSTGRES_PASSWORD:?}"

psql \
  --host postgresql \
  --username temporal \
  --dbname postgres \
  --quiet \
  --set ON_ERROR_STOP=1 \
  --set "litellm_password=${LITELLM_DATABASE_PASSWORD}" <<'SQL'
SELECT format(
  'CREATE ROLE litellm LOGIN PASSWORD %L',
  :'litellm_password'
)
WHERE NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'litellm')
\gexec

ALTER ROLE litellm WITH LOGIN PASSWORD :'litellm_password' NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION;

SELECT 'CREATE DATABASE litellm OWNER litellm'
WHERE NOT EXISTS (SELECT 1 FROM pg_database WHERE datname = 'litellm')
\gexec

REVOKE ALL ON DATABASE temporal FROM litellm;
REVOKE ALL ON DATABASE temporal_visibility FROM litellm;
REVOKE CONNECT ON DATABASE temporal FROM PUBLIC;
REVOKE CONNECT ON DATABASE temporal_visibility FROM PUBLIC;
GRANT ALL PRIVILEGES ON DATABASE litellm TO litellm;
SQL
