from cartei_db.base import (
    AUDIT_FUNCTION_SQL, create_audit_trigger_sql, drop_audit_trigger_sql,
)


def test_function_sql_shape():
    assert "CREATE OR REPLACE FUNCTION audit_history()" in AUDIT_FUNCTION_SQL
    assert "to_jsonb(OLD)" in AUDIT_FUNCTION_SQL
    assert "current_setting('cartei.changed_by', true)" in AUDIT_FUNCTION_SQL
    assert "AFTER" not in AUDIT_FUNCTION_SQL  # the function itself is not a trigger def


def test_trigger_sql_with_exclusion():
    sql = create_audit_trigger_sql("tenant", {"is_flinta"})
    assert "CREATE OR REPLACE TRIGGER tenant_audit" in sql
    assert "AFTER UPDATE OR DELETE ON tenant" in sql
    assert "EXECUTE FUNCTION audit_history('is_flinta')" in sql


def test_trigger_sql_without_exclusion():
    sql = create_audit_trigger_sql("room")
    assert "EXECUTE FUNCTION audit_history()" in sql


def test_drop_trigger_sql():
    assert drop_audit_trigger_sql("room") == "DROP TRIGGER IF EXISTS room_audit ON room;"


def test_python_listeners_removed():
    import cartei_db.base as base
    assert not hasattr(base, "_on_update")
    assert not hasattr(base, "_jsonify")
