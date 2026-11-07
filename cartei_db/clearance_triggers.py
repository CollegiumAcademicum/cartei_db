"""Immutability enforcement for confidentiality_clearance_event.

A clearance approval row is written once and must never be
updated or deleted — tamper-evidence is the whole point of the log. The trigger
fires for the table owner too (unlike GRANTs/RLS), so the invariant holds
regardless of connecting role. SQL is shared by the Alembic migration and the
test conftest."""

TABLE = "confidentiality_clearance_event"

_FUNCTION = """
CREATE OR REPLACE FUNCTION confidentiality_clearance_event_immutable() RETURNS trigger AS $$
BEGIN
    RAISE EXCEPTION 'confidentiality_clearance_event rows are append-only (no update or delete)';
END;
$$ LANGUAGE plpgsql;
"""


def clearance_event_immutable_sql() -> list[str]:
    return [
        _FUNCTION,
        f"CREATE OR REPLACE TRIGGER {TABLE}_immutable "
        f"BEFORE UPDATE OR DELETE ON {TABLE} "
        f"FOR EACH ROW EXECUTE FUNCTION confidentiality_clearance_event_immutable();",
    ]


def drop_clearance_event_immutable_sql() -> list[str]:
    return [
        f"DROP TRIGGER IF EXISTS {TABLE}_immutable ON {TABLE}",
        "DROP FUNCTION IF EXISTS confidentiality_clearance_event_immutable()",
    ]
