"""Immutability enforcement for ag_membership_event (same pattern as
clearance_triggers). SQL is shared by the Alembic migration and the test conftest."""

TABLE = "ag_membership_event"

_FUNCTION = """
CREATE OR REPLACE FUNCTION ag_membership_event_immutable() RETURNS trigger AS $$
BEGIN
    RAISE EXCEPTION 'ag_membership_event rows are append-only (no update or delete)';
END;
$$ LANGUAGE plpgsql;
"""


def ag_membership_event_immutable_sql() -> list[str]:
    return [
        _FUNCTION,
        f"CREATE OR REPLACE TRIGGER {TABLE}_immutable "
        f"BEFORE UPDATE OR DELETE ON {TABLE} "
        f"FOR EACH ROW EXECUTE FUNCTION ag_membership_event_immutable();",
    ]


def drop_ag_membership_event_immutable_sql() -> list[str]:
    return [
        f"DROP TRIGGER IF EXISTS {TABLE}_immutable ON {TABLE}",
        "DROP FUNCTION IF EXISTS ag_membership_event_immutable()",
    ]
