"""Append-only enforcement for the `document` table.

A submitted document is immutable except for a single revocation: revoked_at
goes NULL -> a value exactly once, together with revoked_by_id and a non-empty
revoked_note. No other column may change, and rows may never be deleted. The
trigger fires for the table owner too, unlike GRANTs/RLS, so this holds
regardless of the connecting role. SQL is shared by the Alembic migration and
the test conftest.
"""

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
        RAISE EXCEPTION 'the only permitted update to document is a revocation';
    END IF;
    IF NEW.revoked_note IS NULL OR btrim(NEW.revoked_note) = '' THEN
        RAISE EXCEPTION 'revoking a document requires a revoked_note';
    END IF;
    IF (to_jsonb(NEW) - 'revoked_at' - 'revoked_by_id' - 'revoked_note')
       IS DISTINCT FROM (to_jsonb(OLD) - 'revoked_at' - 'revoked_by_id' - 'revoked_note') THEN
        RAISE EXCEPTION 'revocation may not change any other column of document';
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;
"""

_TRIGGER = """
CREATE OR REPLACE TRIGGER document_append_only
    BEFORE UPDATE OR DELETE ON document
    FOR EACH ROW EXECUTE FUNCTION document_append_only();
"""


def document_append_only_sql() -> list[str]:
    return [_FUNCTION, _TRIGGER]


def drop_document_append_only_sql() -> list[str]:
    return [
        "DROP TRIGGER IF EXISTS document_append_only ON document",
        "DROP FUNCTION IF EXISTS document_append_only()",
    ]
