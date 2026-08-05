#!/usr/bin/env bash
set -e

# shellcheck source=.env
[ -f .env ] && set -a && source .env && set +a

export DATABASE_URL="${DATABASE_URL:-postgresql+psycopg://cartei:cartei@localhost:5432/cartei}"
export POSTGRES_DSN="${POSTGRES_DSN:-postgresql://cartei:cartei@localhost:5432/cartei}"

docker compose up -d
uv run alembic revision --autogenerate -m "${1:-initial}"
uv run alembic upgrade head

psql "$POSTGRES_DSN" \
  --variable="AG_ABFRAGE_PASSWORD=${AG_ABFRAGE_PASSWORD:?AG_ABFRAGE_PASSWORD not set in .env}" \
  --file=db-grants.sql
