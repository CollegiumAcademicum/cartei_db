"""No-delete enforcement for the damage tables (room_damage, wg_damage).

A damage row may never be deleted; the only lifecycle mutation is marking it
fixed (set fixed_at) or reopening it (clear fixed_at), plus ordinary note/size
edits — all UPDATEs pass. The trigger fires for the table owner too (unlike
GRANTs/RLS), so the invariant holds regardless of connecting role. SQL is shared
by the Alembic migration and the test conftest."""

DAMAGE_TABLES = ("room_damage", "wg_damage")

_FUNCTION = """
CREATE OR REPLACE FUNCTION damage_no_delete() RETURNS trigger AS $$
BEGIN
    RAISE EXCEPTION 'damage rows may not be deleted; mark fixed instead';
END;
$$ LANGUAGE plpgsql;
"""


def _trigger_sql(table: str) -> str:
    return (
        f"CREATE OR REPLACE TRIGGER {table}_no_delete "
        f"BEFORE DELETE ON {table} "
        f"FOR EACH ROW EXECUTE FUNCTION damage_no_delete();"
    )


def damage_no_delete_sql(tables: tuple[str, ...] = DAMAGE_TABLES) -> list[str]:
    return [_FUNCTION] + [_trigger_sql(t) for t in tables]


def drop_damage_no_delete_sql(tables: tuple[str, ...] = DAMAGE_TABLES) -> list[str]:
    return [f"DROP TRIGGER IF EXISTS {t}_no_delete ON {t}" for t in tables] + [
        "DROP FUNCTION IF EXISTS damage_no_delete()"
    ]
