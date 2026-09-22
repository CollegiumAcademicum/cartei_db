#!/usr/bin/env bash
set -e

# shellcheck source=.env
[ -f .env ] && set -a && source .env && set +a

export DATABASE_URL="${DATABASE_URL:-postgresql+psycopg://cartei:cartei@localhost:5432/cartei}"
export POSTGRES_DSN="${POSTGRES_DSN:-postgresql://cartei:cartei@localhost:5432/cartei}"

docker compose up -d
until docker compose exec -T db pg_isready -U cartei >/dev/null 2>&1; do sleep 1; done
uv run alembic upgrade head

psql "$POSTGRES_DSN" \
  --variable="AG_ABFRAGE_PASSWORD=${AG_ABFRAGE_PASSWORD:?AG_ABFRAGE_PASSWORD not set in .env}" \
  --file=db-grants.sql
