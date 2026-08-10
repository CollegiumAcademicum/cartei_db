# DB-level audit triggers

Date: 2026-08-10
Repos: `cartei_db` (trigger + audit core) and `CArtei` (actor middleware)

## Problem

`entity_history` auditing lives entirely in SQLAlchemy `before_update` /
`before_delete` event listeners on `Historized` (`cartei_db/base.py`). Only
writes routed through a SQLAlchemy session are captured. CArtei writes via the
Django ORM and raw `connection.cursor()` — both bypass the listeners, so tenant
edits and the existing `abfragen.py` writes produce **no** history. History is a
hard requirement, so auditing must move **below both ORMs** into the database.

## Approach

A single generic Postgres trigger function `audit_history()`, attached AFTER
UPDATE OR DELETE to every audited table, snapshots the **old** row into
`entity_history`. Every writer — Django ORM, raw SQL, SQLAlchemy, psql — is
captured in one place. The actor (`changed_by` / `change_source`) is passed per
transaction via a Postgres custom setting (`cartei.changed_by`,
`cartei.change_source`) that each application sets at its request/transaction
boundary; the trigger reads it with `current_setting(..., true)`.

The Python listeners are **removed** (they would double-write). cartei_db keeps
its `changed_by_var` / `change_source_var` contextvar API — a SQLAlchemy
`after_begin` listener now translates those contextvars into the session setting
instead of writing history directly.

## Audited tables

The three current `Historized` models: `tenant` (excludes `is_flinta`),
`ag_abfrage_result`, `room`. Exclusions come from `__history_exclude__` and are
passed to the trigger as arguments.

## The trigger function

```sql
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
    RETURN NULL;  -- AFTER trigger: return value ignored
END;
$$ LANGUAGE plpgsql;
```

Per-table trigger, e.g. tenant (excludes `is_flinta`):

```sql
CREATE TRIGGER tenant_audit AFTER UPDATE OR DELETE ON tenant
    FOR EACH ROW EXECUTE FUNCTION audit_history('is_flinta');
```

`ag_abfrage_result` and `room` get the same with no exclusion args.

Snapshot = `to_jsonb(OLD)` — the row state **before** the change (matches
today's behavior of storing old values). `entity_id = OLD.id` (all three tables
have `id`).

## Actor passing

Both apps set the actor inside the writing transaction using `set_config(name,
value, is_local=true)` (the parametrizable form of `SET LOCAL`):

- **cartei_db** — a `Session` `after_begin` listener runs
  `SELECT set_config('cartei.changed_by', <changed_by_var>, true)` and the same
  for `change_source`. Contextvar API unchanged for services.
- **CArtei** — `AuditActorMiddleware` wraps each authenticated request in
  `transaction.atomic()` and runs `set_config('cartei.changed_by', <username>,
  true)` + `change_source = 'HUMAN'`. Guards on `connection.vendor ==
  'postgresql'` so the SQLite test DB is unaffected. Retroactively audits every
  Django write, including `abfragen.py`.

Unset setting → `coalesce` defaults to `system` / `SERVICE`, matching the
contextvar defaults.

## Shared trigger DDL

The function/trigger SQL is a reusable constant + helper in `cartei_db.base`
(`AUDIT_FUNCTION_SQL`, `create_audit_trigger_sql(table, exclude)`,
`drop_audit_trigger_sql(table)`), consumed by **both** the Alembic migration and
the test fixture — the test DB is built via `create_all` (no migrations), so the
fixture installs the same triggers the migration will.

## base.py changes

- Remove `_on_update`, `_on_delete`, and the two `event.listen(Historized, ...)`
  registrations.
- Remove `_jsonify` (dead once snapshotting is `to_jsonb`) and its tests.
- Keep `Historized` (marker + `__history_exclude__`), `EntityHistory`, the
  contextvars, `ChangeSource`.
- Add `AUDIT_FUNCTION_SQL`, `create_audit_trigger_sql`, `drop_audit_trigger_sql`,
  and the `Session` `after_begin` actor listener.

## Accepted consequences

- **Snapshot format shift:** `to_jsonb(OLD)` renders `Numeric` (e.g.
  `soli_miete_wunsch`) as a JSON number; the old Python path stored `Decimal` as
  a string. New rows are self-consistent; only pre-migration rows differ.
  Dates/timestamps/bools/uuids render the same either way.
- **Test rewrite:** `tests/test_base.py` currently asserts the Python listeners
  against a `_Thing` table built by `create_all`. It is reworked to assert
  trigger-written history, with the fixture installing triggers on all
  `Historized` test tables. `_jsonify` tests are dropped.

## Testing

- **cartei_db** (live Postgres): update on a `Historized` test row writes one
  `entity_history` snapshot of the old values; delete writes a snapshot;
  excluded column absent; actor comes from the contextvars via `set_config`;
  default actor is `system`/`SERVICE` when unset.
- **CArtei** (SQLite): middleware wraps authenticated requests and calls
  `set_config` with the username on Postgres; no-ops for anonymous requests and
  on non-Postgres vendors (asserted via spy). Full trigger audit is proven in
  cartei_db, not re-tested against SQLite.

## Out of scope

- Backfilling/reformatting pre-migration `entity_history` rows.
- A history-viewing UI (separate feature).
- Auditing tables not currently `Historized`.

## Dependency

The tenant-view feature
(`CArtei/docs/superpowers/specs/2026-08-10-tenant-view-role-sections-design.md`)
depends on this: once shipped, its Django edits are audited with no view-level
code. That spec's "audit gap" note is superseded.
