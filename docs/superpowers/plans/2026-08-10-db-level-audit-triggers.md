# DB-Level Audit Triggers Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Move `entity_history` auditing from SQLAlchemy Python listeners into a Postgres trigger so every writer (Django ORM, raw SQL, SQLAlchemy) is captured, with the actor passed per-transaction via a Postgres custom setting.

**Architecture:** One generic `audit_history()` trigger function attached AFTER UPDATE OR DELETE to `tenant`, `ag_abfrage_result`, `room`. It snapshots `to_jsonb(OLD)` (minus `__history_exclude__` columns passed as trigger args) into `entity_history`, reading `changed_by`/`change_source` from `current_setting('cartei.*', true)`. cartei_db sets those via a `Session` `after_begin` listener from the existing contextvars; CArtei sets them via `AuditActorMiddleware`. The Python listeners are removed.

**Tech Stack:** SQLAlchemy 2.0, Alembic, PostgreSQL (plpgsql), Django 5, pytest. Python 3.14, `uv`.

## Global Constraints

- Run with `uv run ...`. cartei_db tests need live Postgres: `DATABASE_URL=postgresql+psycopg://cartei:cartei@localhost:5432/cartei uv run pytest`.
- Audited tables and exclusions come from `__history_exclude__`: `tenant` → `{"is_flinta"}`, `ag_abfrage_result` → none, `room` → none.
- Snapshot stores the **old** row state (before the change), `entity_id = OLD.id`.
- Actor is set with `set_config(name, value, true)` (transaction-local) — never string-interpolate the value.
- The trigger DDL is a single shared source in `cartei_db.base`, reused by the migration and the test fixture (test DB is built via `create_all`, not migrations).
- CArtei middleware guards on `connection.vendor == 'postgresql'` so the SQLite test DB is unaffected.
- Unset setting defaults to `system` / `SERVICE` via `coalesce`.

---

### Task 1: Audit SQL + actor listener in `cartei_db.base`; remove Python listeners

**Files:**
- Modify: `cartei_db/base.py`
- Test: `tests/test_audit_sql.py` (unit — string shape, no DB)

**Interfaces:**
- Produces:
  - `AUDIT_FUNCTION_SQL: str` — `CREATE OR REPLACE FUNCTION audit_history() ...`
  - `create_audit_trigger_sql(table: str, exclude: set[str] = frozenset()) -> str`
  - `drop_audit_trigger_sql(table: str) -> str`
  - `Session` `after_begin` listener setting `cartei.changed_by` / `cartei.change_source` from `changed_by_var` / `change_source_var`.
- Removes: `_on_update`, `_on_delete`, `_jsonify`, the two `event.listen(Historized, ...)` calls.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_audit_sql.py
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
    assert "CREATE TRIGGER tenant_audit" in sql
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_audit_sql.py -v`
Expected: FAIL — `ImportError` on `AUDIT_FUNCTION_SQL`.

- [ ] **Step 3: Edit `cartei_db/base.py`**

Remove `_jsonify`, `_on_update`, `_on_delete`, and both `event.listen(Historized, ...)` lines. Keep `EntityHistory`, `Historized`, contextvars. Add:

```python
from sqlalchemy.orm import Session

AUDIT_FUNCTION_SQL = """
CREATE OR REPLACE FUNCTION audit_history() RETURNS trigger AS $$
DECLARE
    snap jsonb;
    col  text;
BEGIN
    snap := to_jsonb(OLD);
    FOREACH col IN ARRAY TG_ARGV LOOP
        snap := snap - col;
    END LOOP;
    INSERT INTO entity_history(entity_type, entity_id, snapshot, changed_at, changed_by, change_source)
    VALUES (
        TG_TABLE_NAME, OLD.id, snap, now(),
        coalesce(current_setting('cartei.changed_by', true), 'system'),
        coalesce(current_setting('cartei.change_source', true), 'SERVICE')
    );
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;
"""


def create_audit_trigger_sql(table: str, exclude: set[str] = frozenset()) -> str:
    args = ", ".join(repr(c) for c in sorted(exclude))
    return (
        f"CREATE TRIGGER {table}_audit AFTER UPDATE OR DELETE ON {table} "
        f"FOR EACH ROW EXECUTE FUNCTION audit_history({args});"
    )


def drop_audit_trigger_sql(table: str) -> str:
    return f"DROP TRIGGER IF EXISTS {table}_audit ON {table};"


@event.listens_for(Session, "after_begin")
def _set_audit_actor(session, transaction, connection) -> None:
    connection.exec_driver_sql(
        "SELECT set_config('cartei.changed_by', %s, true)", (changed_by_var.get(),)
    )
    connection.exec_driver_sql(
        "SELECT set_config('cartei.change_source', %s, true)",
        (change_source_var.get().value,),
    )
```

Keep the `Historized` class (marker only) and the `from sqlalchemy import ... event` import.

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_audit_sql.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add cartei_db/base.py tests/test_audit_sql.py
git commit -m "feat: DB audit trigger SQL + actor listener; drop Python history listeners"
```

---

### Task 2: Install triggers in the test fixture; rewrite `test_base.py`

The test DB is built with `create_all` (no migrations). Install the shared trigger SQL on every `Historized` table after `create_all`, then assert trigger-driven history.

**Files:**
- Modify: `tests/conftest.py` (the `engine` fixture)
- Rewrite: `tests/test_base.py`

**Interfaces:**
- Consumes: `AUDIT_FUNCTION_SQL`, `create_audit_trigger_sql` from `cartei_db.base`; `Historized.__subclasses__()`.

- [ ] **Step 1: Update the `engine` fixture**

In `tests/conftest.py`, after `Base.metadata.create_all(eng)` add trigger install; before `drop_all` add trigger teardown (optional — drop_all removes tables anyway, but drop the function):

```python
from sqlalchemy import text
from cartei_db.base import (
    Base, Historized, AUDIT_FUNCTION_SQL, create_audit_trigger_sql,
)

@pytest.fixture(scope="session")
def engine():
    eng = create_engine(os.environ["DATABASE_URL"])
    Base.metadata.create_all(eng)
    with eng.begin() as conn:
        conn.execute(text(AUDIT_FUNCTION_SQL))
        for cls in Historized.__subclasses__():
            conn.execute(text(create_audit_trigger_sql(
                cls.__tablename__, getattr(cls, "__history_exclude__", set())
            )))
    yield eng
    Base.metadata.drop_all(eng)
    with eng.begin() as conn:
        conn.execute(text("DROP FUNCTION IF EXISTS audit_history() CASCADE"))
    eng.dispose()
```

Keep the existing `session` fixture as-is.

- [ ] **Step 2: Rewrite `tests/test_base.py`**

Replace the `_jsonify`/listener tests. Keep the `_Thing` model and the contextvar-default test. Note: the `session` fixture wraps everything in a rolled-back outer transaction with savepoints; the trigger fires on `flush()` within that transaction, so the `entity_history` row is visible to the same session before rollback.

```python
from sqlalchemy import Column, Integer, String

from cartei_db.base import Base, EntityHistory, Historized, changed_by_var, change_source_var
from cartei_db.enums import ChangeSource


class _Thing(Historized, Base):
    __tablename__ = "_test_thing"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String)
    secret = Column(String)
    __history_exclude__ = {"secret"}


def test_context_var_defaults():
    assert changed_by_var.get() == "system"
    assert change_source_var.get() == ChangeSource.SERVICE


def test_history_written_on_update(session):
    thing = _Thing(name="original", secret="hidden")
    session.add(thing)
    session.flush()

    thing.name = "updated"
    session.flush()

    rows = session.query(EntityHistory).filter_by(
        entity_type="_test_thing", entity_id=thing.id
    ).all()
    assert len(rows) == 1
    assert rows[0].snapshot["name"] == "original"   # old value
    assert "secret" not in rows[0].snapshot          # excluded column
    assert rows[0].changed_by == "system"            # default when unset
    assert rows[0].change_source == "SERVICE"


def test_history_written_on_delete(session):
    thing = _Thing(name="to_delete", secret="hidden")
    session.add(thing)
    session.flush()

    session.delete(thing)
    session.flush()

    row = session.query(EntityHistory).filter_by(
        entity_type="_test_thing", entity_id=thing.id
    ).one()
    assert row.snapshot["name"] == "to_delete"
    assert "secret" not in row.snapshot


def test_actor_from_context_var(session):
    token = changed_by_var.set("pbartz")
    src = change_source_var.set(ChangeSource.HUMAN)
    try:
        thing = _Thing(name="test")
        session.add(thing)
        session.flush()
        thing.name = "changed"
        session.flush()
        row = session.query(EntityHistory).filter_by(
            entity_type="_test_thing", entity_id=thing.id
        ).one()
        assert row.changed_by == "pbartz"
        assert row.change_source == "HUMAN"
    finally:
        changed_by_var.reset(token)
        change_source_var.reset(src)
```

Note: `test_actor_from_context_var` requires the `after_begin` listener to have set the GUC when the session's transaction began. Because contextvars are read at `after_begin`, set them **before** the first flush opens the transaction — the fixture's `session` begins its transaction lazily on first use, so setting the var at the top of the test (before `session.add`) is correct. If the listener already fired with defaults, add an explicit `session.begin_nested()`-free reproduction is unnecessary; the savepoint mode re-emits `after_begin` per transaction. If flakiness appears, set the contextvars in a fixture that runs before `session`.

- [ ] **Step 3: Run tests to verify they pass**

Run: `DATABASE_URL=postgresql+psycopg://cartei:cartei@localhost:5432/cartei uv run pytest tests/test_base.py -v`
Expected: PASS (4 tests).

- [ ] **Step 4: Commit**

```bash
git add tests/conftest.py tests/test_base.py
git commit -m "test: assert trigger-driven auditing; install triggers in fixture"
```

---

### Task 3: Alembic migration for function + triggers

**Files:**
- Create: `migrations/versions/<rev>_add_audit_triggers.py` (via autogenerate scaffold, then hand-write ops)
- Test: covered by Task 2 behavior + a migration round-trip check below.

**Interfaces:**
- Consumes: `AUDIT_FUNCTION_SQL`, `create_audit_trigger_sql`, `drop_audit_trigger_sql` from `cartei_db.base`.

- [ ] **Step 1: Generate an empty revision**

Run: `DATABASE_URL=postgresql+psycopg://cartei:cartei@localhost:5432/cartei uv run alembic revision -m "add audit triggers"`
This creates `migrations/versions/<rev>_add_audit_triggers.py`. (No `--autogenerate` — there is no schema/table diff, only DDL for functions/triggers.)

- [ ] **Step 2: Write the migration body**

```python
from alembic import op

from cartei_db.base import (
    AUDIT_FUNCTION_SQL, create_audit_trigger_sql, drop_audit_trigger_sql,
)

# revision identifiers filled by alembic scaffold — keep them.

_AUDITED = {"tenant": {"is_flinta"}, "ag_abfrage_result": set(), "room": set()}


def upgrade() -> None:
    op.execute(AUDIT_FUNCTION_SQL)
    for table, exclude in _AUDITED.items():
        op.execute(create_audit_trigger_sql(table, exclude))


def downgrade() -> None:
    for table in _AUDITED:
        op.execute(drop_audit_trigger_sql(table))
    op.execute("DROP FUNCTION IF EXISTS audit_history() CASCADE")
```

- [ ] **Step 3: Apply and verify the migration round-trips**

```bash
export DATABASE_URL=postgresql+psycopg://cartei:cartei@localhost:5432/cartei
uv run alembic upgrade head
uv run alembic downgrade -1
uv run alembic upgrade head
```
Expected: all succeed with no error. After the final `upgrade`, verify the trigger exists:

Run:
```bash
psql "$DATABASE_URL" -c "SELECT tgname FROM pg_trigger WHERE tgname LIKE '%_audit';"
```
Expected: `tenant_audit`, `ag_abfrage_result_audit`, `room_audit` listed.

- [ ] **Step 4: Commit**

```bash
git add migrations/versions/*_add_audit_triggers.py
git commit -m "feat: migration adding audit_history function and table triggers"
```

---

### Task 4: `AuditActorMiddleware` in CArtei

This task is in the **CArtei** repo.

**Files:**
- Create: `app/middleware.py`
- Modify: `cartei/settings.py` (append to `MIDDLEWARE`)
- Test: `tests/test_audit_middleware.py`

**Interfaces:**
- Produces: `AuditActorMiddleware` that, for authenticated requests on a Postgres connection, sets `cartei.changed_by = request.user.username` and `cartei.change_source = 'HUMAN'` inside a request-wrapping `transaction.atomic()`.

- [ ] **Step 1: Write the failing test**

The CArtei test DB is SQLite, so assert the middleware calls `set_config` with the right args (spied) on Postgres and no-ops otherwise.

```python
# tests/test_audit_middleware.py
from unittest.mock import MagicMock, patch

import pytest

from app.middleware import AuditActorMiddleware, _set_audit_actor


class _User:
    def __init__(self, authed, username="pbartz"):
        self.is_authenticated = authed
        self.username = username


def test_set_audit_actor_noop_on_sqlite():
    conn = MagicMock()
    conn.vendor = "sqlite"
    _set_audit_actor(conn, "pbartz")
    conn.cursor.assert_not_called()


def test_set_audit_actor_runs_on_postgres():
    conn = MagicMock()
    conn.vendor = "postgresql"
    cursor = conn.cursor.return_value.__enter__.return_value
    _set_audit_actor(conn, "pbartz")
    calls = [c.args for c in cursor.execute.call_args_list]
    assert any("set_config('cartei.changed_by'" in a[0] and a[1] == ["pbartz"] for a in calls)
    assert any("set_config('cartei.change_source'" in a[0] and a[1] == ["HUMAN"] for a in calls)


def test_middleware_skips_anonymous():
    get_response = MagicMock(return_value="resp")
    mw = AuditActorMiddleware(get_response)
    request = MagicMock()
    request.user = _User(authed=False)
    with patch("app.middleware._set_audit_actor") as spy:
        assert mw(request) == "resp"
        spy.assert_not_called()


def test_middleware_sets_actor_for_authenticated():
    get_response = MagicMock(return_value="resp")
    mw = AuditActorMiddleware(get_response)
    request = MagicMock()
    request.user = _User(authed=True, username="pbartz")
    with patch("app.middleware._set_audit_actor") as spy:
        assert mw(request) == "resp"
        spy.assert_called_once()
        assert spy.call_args.args[1] == "pbartz"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_audit_middleware.py -v`
Expected: FAIL — `ModuleNotFoundError: app.middleware`.

- [ ] **Step 3: Write `app/middleware.py`**

```python
from django.db import connection, transaction


def _set_audit_actor(conn, username: str, source: str = "HUMAN") -> None:
    # Trigger-based audit reads these Postgres settings; SQLite (tests) has no set_config.
    if conn.vendor != "postgresql":
        return
    with conn.cursor() as c:
        c.execute("SELECT set_config('cartei.changed_by', %s, true)", [username])
        c.execute("SELECT set_config('cartei.change_source', %s, true)", [source])


class AuditActorMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if not getattr(request.user, "is_authenticated", False):
            return self.get_response(request)
        with transaction.atomic():
            _set_audit_actor(connection, request.user.username)
            return self.get_response(request)
```

- [ ] **Step 4: Register the middleware**

In `cartei/settings.py`, append to `MIDDLEWARE` (after `AuthenticationMiddleware` so `request.user` is populated):

```python
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "app.middleware.AuditActorMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `uv run pytest tests/test_audit_middleware.py -v`
Expected: PASS (4 tests).

- [ ] **Step 6: Run the full CArtei suite for regressions**

Run: `uv run pytest -q`
Expected: PASS.

- [ ] **Step 7: Commit**

```bash
git add app/middleware.py cartei/settings.py tests/test_audit_middleware.py
git commit -m "feat: AuditActorMiddleware sets DB audit actor per request"
```

---

## Self-Review

**Spec coverage:**
- Generic trigger function + per-table triggers with exclusions → Tasks 1, 3. ✓
- Snapshot of old row, `entity_id = OLD.id`, coalesce defaults → Task 1 SQL, Task 2 tests. ✓
- Remove Python listeners + `_jsonify` → Task 1 (+ `test_python_listeners_removed`). ✓
- Actor via `set_config` from contextvars (cartei_db) → Task 1 listener, Task 2 `test_actor_from_context_var`. ✓
- Actor via middleware (CArtei), Postgres-guarded → Task 4. ✓
- Shared DDL reused by migration + fixture → Task 1 constants, Tasks 2 & 3 consume. ✓
- Audited set = tenant/ag_abfrage_result/room with tenant excluding is_flinta → Task 3 `_AUDITED`. ✓
- Test rewrite + fixture trigger install → Task 2. ✓

**Placeholder scan:** None — all steps carry runnable code and explicit expected output. The Alembic revision id is scaffold-generated (noted, not a placeholder).

**Type consistency:** `AUDIT_FUNCTION_SQL`, `create_audit_trigger_sql(table, exclude)`, `drop_audit_trigger_sql(table)`, `_set_audit_actor(conn, username, source)`, `AuditActorMiddleware` — names identical across Tasks 1–4.

**Known follow-ups (out of scope):** backfill of old-format rows; history-viewing UI; auditing further tables.
