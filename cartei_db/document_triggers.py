"""Append-only enforcement for the per-type document tables
(datenschutz_document, photoerlaubnis_document, ...).

A submitted document is immutable except for a single revocation: revoked_at
goes NULL -> a value exactly once, together with revoked_by_id and a non-empty
revoked_note. No other column may change, and rows may never be deleted. The
trigger function is row-shape-agnostic (it works off the revoked_* columns and
to_jsonb), so one function serves every document table and each table gets its
own trigger. The trigger fires for the table owner too, unlike GRANTs/RLS, so
this holds regardless of the connecting role. SQL is shared by the Alembic
migration and the test conftest.
"""

# Every per-type document table that carries the append-only invariant.
DOCUMENT_TABLES = (
    "datenschutz_document",
    "photoerlaubnis_document",
    "vertraulichkeitserklaerung_document",
    "mietvertrag_document",
    "mietbedingungen_document",
    "wohnungsgeberbescheinigung_document",
    "sepa_lastschriftmandat_document",
    "bescheid_ausbildungsstelle_document",
    "selbstverpflichtung_engagement_document",
)

_FUNCTION = """
CREATE OR REPLACE FUNCTION document_append_only() RETURNS trigger AS $$
BEGIN
    IF TG_OP = 'DELETE' THEN
        RAISE EXCEPTION 'document rows are append-only; revoke instead of deleting';
    END IF;
    IF OLD.revoked_at IS NOT NULL THEN
        RAISE EXCEPTION 'document % is already revoked and immutable', OLD.id;
    END IF;
    IF NEW.revoked_at IS NULL THEN
        RAISE EXCEPTION 'the only permitted update to a document is a revocation';
    END IF;
    IF NEW.revoked_note IS NULL OR btrim(NEW.revoked_note) = '' THEN
        RAISE EXCEPTION 'revoking a document requires a revoked_note';
    END IF;
    IF (to_jsonb(NEW) - 'revoked_at' - 'revoked_by_id' - 'revoked_note')
       IS DISTINCT FROM (to_jsonb(OLD) - 'revoked_at' - 'revoked_by_id' - 'revoked_note') THEN
        RAISE EXCEPTION 'revocation may not change any other column of a document';
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;
"""


def _trigger_sql(table: str) -> str:
    return (
        f"CREATE OR REPLACE TRIGGER {table}_append_only "
        f"BEFORE UPDATE OR DELETE ON {table} "
        f"FOR EACH ROW EXECUTE FUNCTION document_append_only();"
    )


def document_append_only_sql(tables: tuple[str, ...] = DOCUMENT_TABLES) -> list[str]:
    return [_FUNCTION] + [_trigger_sql(t) for t in tables]


def drop_document_append_only_sql(tables: tuple[str, ...] = DOCUMENT_TABLES) -> list[str]:
    return [f"DROP TRIGGER IF EXISTS {t}_append_only ON {t}" for t in tables] + [
        "DROP FUNCTION IF EXISTS document_append_only()"
    ]
