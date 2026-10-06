"""Immutability enforcement for impersonation_event.

An impersonation audit row is written once (on start, on stop) and must never be
updated or deleted — tamper-evidence is the whole point of the log. The trigger
fires for the table owner too (unlike GRANTs/RLS), so the invariant holds
regardless of connecting role. SQL is shared by the Alembic migration and the
test conftest."""

TABLE = "impersonation_event"

_FUNCTION = """
CREATE OR REPLACE FUNCTION impersonation_event_immutable() RETURNS trigger AS $$
BEGIN
    RAISE EXCEPTION 'impersonation_event rows are append-only (no update or delete)';
END;
$$ LANGUAGE plpgsql;
"""


def impersonation_event_immutable_sql() -> list[str]:
    return [
        _FUNCTION,
        f"CREATE OR REPLACE TRIGGER {TABLE}_immutable "
        f"BEFORE UPDATE OR DELETE ON {TABLE} "
        f"FOR EACH ROW EXECUTE FUNCTION impersonation_event_immutable();",
    ]


def drop_impersonation_event_immutable_sql() -> list[str]:
    return [
        f"DROP TRIGGER IF EXISTS {TABLE}_immutable ON {TABLE}",
        "DROP FUNCTION IF EXISTS impersonation_event_immutable()",
    ]
