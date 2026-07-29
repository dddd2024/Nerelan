#!/bin/sh
set -eu

: "${POSTGRES_SEEDS:?POSTGRES_SEEDS is required}"
: "${POSTGRES_USER:?POSTGRES_USER is required}"
: "${SQL_PASSWORD:?SQL_PASSWORD is required}"

nc -z -w 10 "${POSTGRES_SEEDS}" "${DB_PORT:-5432}"

ensure_schema() {
    database="$1"
    schema_directory="$2"

    temporal-sql-tool --plugin postgres12 --ep "${POSTGRES_SEEDS}" \
        -u "${POSTGRES_USER}" -p "${DB_PORT:-5432}" --db "${database}" \
        --quiet create
    temporal-sql-tool --plugin postgres12 --ep "${POSTGRES_SEEDS}" \
        -u "${POSTGRES_USER}" -p "${DB_PORT:-5432}" --db "${database}" \
        --quiet setup-schema -v 0.0
    temporal-sql-tool --plugin postgres12 --ep "${POSTGRES_SEEDS}" \
        -u "${POSTGRES_USER}" -p "${DB_PORT:-5432}" --db "${database}" \
        update-schema -d "${schema_directory}"
}

ensure_schema temporal /etc/temporal/schema/postgresql/v12/temporal/versioned
ensure_schema temporal_visibility /etc/temporal/schema/postgresql/v12/visibility/versioned
