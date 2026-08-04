# CArtei DB Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement the `cartei_db` Python package — SQLAlchemy 2.0 models, a JSONB-snapshot history mixin, and Alembic migrations for the CArtei tenant management system's shared PostgreSQL data layer.

**Architecture:** A pure data-layer library with no web framework. All entities live as SQLAlchemy 2.0 mapped classes under `cartei_db/models/`. A `Historized` mixin (in `base.py`) registers `before_update`/`before_delete` SQLAlchemy events that write JSONB snapshots to a single `entity_history` table. Actor context (`changed_by`, `change_source`) is injected by consuming services via `contextvars.ContextVar`. Alembic owns all schema migrations.

**Tech Stack:** Python 3.14, SQLAlchemy ≥ 2.0, Alembic ≥ 1.13, psycopg[binary] ≥ 3.1, pytest ≥ 8.0, PostgreSQL

## Global Constraints

- Python ≥ 3.14 only
- SQLAlchemy 2.0 style throughout: use `Mapped[T]` and `mapped_column()` for all columns; no legacy `Column()` in models
- PostgreSQL dialect features are allowed: JSONB, UUID, LargeBinary (bytea)
- All datetimes stored as UTC with `DateTime(timezone=True)`
- `DATABASE_URL` env var provides the PostgreSQL connection string for both tests and migrations
- Never sign commits with Co-Authored-By or AI attribution
- Tests must use a real PostgreSQL database — no mocking, no SQLite
- Each test runs in its own transaction that is rolled back after the test; use `session.flush()` not `session.commit()` in tests

---

## File Map

```
pyproject.toml                               # modify: add deps + pytest config
cartei_db/__init__.py                        # new: empty package init
cartei_db/enums.py                           # new: AGStatus, ChangeSource, EnrollmentType
cartei_db/base.py                            # new: Base, EntityHistory, Historized mixin, ContextVars
cartei_db/models/__init__.py                 # new: re-exports all models (needed by Alembic autogenerate)
cartei_db/models/building.py                 # new: Building
cartei_db/models/wg.py                       # new: WG
cartei_db/models/room.py                     # new: Room (Historized)
cartei_db/models/tenant.py                   # new: Tenant (Historized)
cartei_db/models/tenant_room_assignment.py   # new: TenantRoomAssignment
cartei_db/models/ag_abfrage.py               # new: AGAbfrage
cartei_db/models/ag_abfrage_result.py        # new: AGAbfrageResult (Historized)
cartei_db/models/enrollment_proof.py         # new: EnrollmentProof
alembic.ini                                  # new: Alembic config
migrations/env.py                            # new: Alembic env, imports all models
migrations/versions/                         # new: populated by Alembic
tests/__init__.py                            # new: empty
tests/conftest.py                            # new: engine + session fixtures
tests/test_enums.py                          # new
tests/test_base.py                           # new: Historized mixin integration test
tests/test_models/__init__.py                # new: empty
tests/test_models/test_building_wg.py        # new
tests/test_models/test_room.py               # new
tests/test_models/test_tenant.py             # new
tests/test_models/test_tenant_room_assignment.py  # new
tests/test_models/test_ag.py                 # new
tests/test_models/test_enrollment_proof.py   # new
```

---

### Task 1: Project scaffolding

**Files:**
- Modify: `pyproject.toml`
- Create: `cartei_db/__init__.py`
- Create: `tests/__init__.py`
- Create: `tests/test_models/__init__.py`
- Create: `tests/conftest.py`

**Interfaces:**
- Produces: `engine` (session-scoped pytest fixture), `session` (function-scoped pytest fixture) — consumed by all test tasks

- [ ] **Step 1: Update pyproject.toml**

Replace the existing `pyproject.toml` with:

```toml
[project]
name = "cartei-db"
version = "0.1.0"
description = "Shared PostgreSQL data layer for CArtei tenant management"
readme = "README.md"
requires-python = ">=3.14"
dependencies = [
    "sqlalchemy>=2.0",
    "alembic>=1.13",
    "psycopg[binary]>=3.1",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0",
]

[tool.pytest.ini_options]
testpaths = ["tests"]
```

- [ ] **Step 2: Install dependencies**

```bash
uv pip install -e ".[dev]"
```

- [ ] **Step 3: Create empty init files**

`cartei_db/__init__.py` — empty file
`tests/__init__.py` — empty file
`tests/test_models/__init__.py` — empty file

- [ ] **Step 4: Write tests/conftest.py**

```python
import os
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session


@pytest.fixture(scope="session")
def engine():
    from cartei_db.base import Base
    # Models are registered in Base.metadata as pytest collects test files.
    # Session-scoped fixture runs after all modules are imported.
    eng = create_engine(os.environ["DATABASE_URL"])
    Base.metadata.create_all(eng)
    yield eng
    Base.metadata.drop_all(eng)
    eng.dispose()


@pytest.fixture
def session(engine):
    connection = engine.connect()
    transaction = connection.begin()
    sess = Session(bind=connection)
    yield sess
    sess.close()
    transaction.rollback()
    connection.close()
```

- [ ] **Step 5: Verify setup collects cleanly**

```bash
export DATABASE_URL=postgresql://postgres:postgres@localhost/cartei_test
pytest --collect-only
```

Expected: 0 tests collected, no import errors.

- [ ] **Step 6: Commit**

```bash
git add pyproject.toml cartei_db/__init__.py tests/__init__.py tests/test_models/__init__.py tests/conftest.py
git commit -m "chore: project scaffolding and test infrastructure"
```

---

### Task 2: Enums

**Files:**
- Create: `cartei_db/enums.py`
- Create: `tests/test_enums.py`

**Interfaces:**
- Produces:
  - `AGStatus` — values: `ACTIVE`, `NOT_ACTIVE_ENOUGH`, `CONTACTED`, `INACTIVE`
  - `ChangeSource` — values: `HUMAN`, `SERVICE`
  - `EnrollmentType` — values: `STUDY`, `APPRENTICESHIP`

- [ ] **Step 1: Write failing tests**

```python
# tests/test_enums.py
from cartei_db.enums import AGStatus, ChangeSource, EnrollmentType


def test_ag_status_values():
    assert AGStatus.ACTIVE.value == "ACTIVE"
    assert AGStatus.NOT_ACTIVE_ENOUGH.value == "NOT_ACTIVE_ENOUGH"
    assert AGStatus.CONTACTED.value == "CONTACTED"
    assert AGStatus.INACTIVE.value == "INACTIVE"


def test_change_source_values():
    assert ChangeSource.HUMAN.value == "HUMAN"
    assert ChangeSource.SERVICE.value == "SERVICE"


def test_enrollment_type_values():
    assert EnrollmentType.STUDY.value == "STUDY"
    assert EnrollmentType.APPRENTICESHIP.value == "APPRENTICESHIP"
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_enums.py -v
```

Expected: `ImportError` — `cartei_db/enums.py` does not exist.

- [ ] **Step 3: Implement cartei_db/enums.py**

```python
from enum import Enum


class AGStatus(Enum):
    ACTIVE = "ACTIVE"
    NOT_ACTIVE_ENOUGH = "NOT_ACTIVE_ENOUGH"
    CONTACTED = "CONTACTED"
    INACTIVE = "INACTIVE"


class ChangeSource(Enum):
    HUMAN = "HUMAN"
    SERVICE = "SERVICE"


class EnrollmentType(Enum):
    STUDY = "STUDY"
    APPRENTICESHIP = "APPRENTICESHIP"
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/test_enums.py -v
```

Expected: 3 PASS.

- [ ] **Step 5: Commit**

```bash
git add cartei_db/enums.py tests/test_enums.py
git commit -m "feat: add domain enums"
```

---

### Task 3: Base, EntityHistory table, Historized mixin

**Files:**
- Create: `cartei_db/base.py`
- Create: `tests/test_base.py`

**Interfaces:**
- Consumes: `ChangeSource` from `cartei_db.enums`
- Produces:
  - `Base: DeclarativeBase` — all models inherit from this
  - `EntityHistory` — audit table with JSONB snapshots
  - `Historized` — mixin; apply as `class MyModel(Historized, Base):`
  - `changed_by_var: ContextVar[str]` — default `"system"`
  - `change_source_var: ContextVar[ChangeSource]` — default `ChangeSource.SERVICE`
  - `_jsonify(value: Any) -> Any` — serializes Python types to JSON-safe values

- [ ] **Step 1: Write failing tests**

```python
# tests/test_base.py
import uuid
from datetime import date, datetime, timezone
from decimal import Decimal

import pytest
from sqlalchemy import Column, Integer, String

from cartei_db.base import (
    Base, EntityHistory, Historized,
    changed_by_var, change_source_var, _jsonify,
)
from cartei_db.enums import ChangeSource


# Minimal model registered in Base.metadata at collection time.
# pytest imports all test modules before running session-scoped fixtures,
# so this class will be in Base.metadata when engine.create_all() runs.
class _Thing(Historized, Base):
    __tablename__ = "_test_thing"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String)
    secret = Column(String)
    __history_exclude__ = {"secret"}


def test_context_var_defaults():
    assert changed_by_var.get() == "system"
    assert change_source_var.get() == ChangeSource.SERVICE


def test_jsonify_primitives():
    assert _jsonify(None) is None
    assert _jsonify(True) is True
    assert _jsonify(42) == 42
    assert _jsonify(3.14) == 3.14
    assert _jsonify("hello") == "hello"


def test_jsonify_datetime():
    dt = datetime(2024, 1, 15, 12, 0, tzinfo=timezone.utc)
    assert _jsonify(dt) == "2024-01-15T12:00:00+00:00"


def test_jsonify_date():
    assert _jsonify(date(2024, 1, 15)) == "2024-01-15"


def test_jsonify_decimal():
    assert _jsonify(Decimal("12.50")) == "12.50"


def test_jsonify_uuid():
    u = uuid.UUID("12345678-1234-5678-1234-567812345678")
    assert _jsonify(u) == "12345678-1234-5678-1234-567812345678"


def test_jsonify_enum():
    assert _jsonify(ChangeSource.HUMAN) == "HUMAN"


def test_history_written_on_update(session):
    thing = _Thing(name="original", secret="hidden")
    session.add(thing)
    session.flush()

    thing.name = "updated"
    thing.secret = "new_secret"
    session.flush()

    history = session.query(EntityHistory).filter_by(
        entity_type="_test_thing", entity_id=thing.id
    ).one()
    assert history.snapshot["name"] == "original"
    assert "secret" not in history.snapshot
    assert history.changed_by == "system"
    assert history.change_source == "SERVICE"


def test_history_written_on_delete(session):
    thing = _Thing(name="to_delete", secret="hidden")
    session.add(thing)
    session.flush()

    session.delete(thing)
    session.flush()

    history = session.query(EntityHistory).filter_by(
        entity_type="_test_thing", entity_id=thing.id
    ).one()
    assert history.snapshot["name"] == "to_delete"
    assert "secret" not in history.snapshot


def test_changed_by_context_var(session):
    token = changed_by_var.set("pbartz")
    try:
        thing = _Thing(name="test")
        session.add(thing)
        session.flush()
        thing.name = "changed"
        session.flush()
        history = session.query(EntityHistory).filter_by(
            entity_type="_test_thing", entity_id=thing.id
        ).one()
        assert history.changed_by == "pbartz"
    finally:
        changed_by_var.reset(token)
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_base.py -v
```

Expected: `ImportError` — `cartei_db/base.py` does not exist.

- [ ] **Step 3: Implement cartei_db/base.py**

```python
import contextvars
import uuid
from datetime import date, datetime, timezone
from decimal import Decimal
from typing import Any

from sqlalchemy import DateTime, Integer, String, event
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from cartei_db.enums import ChangeSource

changed_by_var: contextvars.ContextVar[str] = contextvars.ContextVar(
    "changed_by", default="system"
)
change_source_var: contextvars.ContextVar[ChangeSource] = contextvars.ContextVar(
    "change_source", default=ChangeSource.SERVICE
)


class Base(DeclarativeBase):
    pass


class EntityHistory(Base):
    __tablename__ = "entity_history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    entity_type: Mapped[str] = mapped_column(String, nullable=False, index=True)
    entity_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    snapshot: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    changed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    changed_by: Mapped[str] = mapped_column(String, nullable=False)
    change_source: Mapped[str] = mapped_column(String, nullable=False)


def _jsonify(value: Any) -> Any:
    if value is None or isinstance(value, (bool, int, float, str)):
        return value
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, uuid.UUID):
        return str(value)
    if hasattr(value, "value"):  # enum
        return value.value
    return str(value)


def _write_to_history(connection, tablename: str, entity_id: int, snapshot: dict[str, Any]) -> None:
    connection.execute(
        EntityHistory.__table__.insert().values(
            entity_type=tablename,
            entity_id=entity_id,
            snapshot=snapshot,
            changed_at=datetime.now(timezone.utc),
            changed_by=changed_by_var.get(),
            change_source=change_source_var.get().value,
        )
    )


def _on_update(mapper, connection, target) -> None:
    from sqlalchemy import inspect as sa_inspect

    exclude = getattr(target.__class__, "__history_exclude__", set())
    insp = sa_inspect(target)
    snapshot: dict[str, Any] = {}

    for col in mapper.columns:
        if col.key in exclude:
            continue
        attr = insp.attrs[col.key]
        hist = attr.history
        # history.deleted holds the old value when an attribute was changed
        if hist.deleted:
            value = hist.deleted[0]
        elif hist.unchanged:
            value = hist.unchanged[0]
        else:
            value = getattr(target, col.key)
        snapshot[col.key] = _jsonify(value)

    _write_to_history(connection, target.__tablename__, target.id, snapshot)


def _on_delete(mapper, connection, target) -> None:
    exclude = getattr(target.__class__, "__history_exclude__", set())
    snapshot = {
        col.key: _jsonify(getattr(target, col.key))
        for col in mapper.columns
        if col.key not in exclude
    }
    _write_to_history(connection, target.__tablename__, target.id, snapshot)


class Historized:
    __history_exclude__: set[str] = set()


event.listen(Historized, "before_update", _on_update, propagate=True)
event.listen(Historized, "before_delete", _on_delete, propagate=True)
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/test_base.py -v
```

Expected: 9 PASS.

- [ ] **Step 5: Commit**

```bash
git add cartei_db/base.py tests/test_base.py
git commit -m "feat: add DeclarativeBase, EntityHistory table, and Historized mixin"
```

---

### Task 4: Building + WG models

**Files:**
- Create: `cartei_db/models/building.py`
- Create: `cartei_db/models/wg.py`
- Create: `tests/test_models/test_building_wg.py`

**Interfaces:**
- Consumes: `Base` from `cartei_db.base`
- Produces:
  - `Building(id: int, name: str)`
  - `WG(id: int, building_id: int, name: str)` with FK → `building.id`

- [ ] **Step 1: Write failing tests**

```python
# tests/test_models/test_building_wg.py
import pytest
from sqlalchemy.exc import IntegrityError

from cartei_db.models.building import Building
from cartei_db.models.wg import WG


def test_create_building(session):
    b = Building(name="Neubau")
    session.add(b)
    session.flush()
    assert b.id is not None
    assert session.get(Building, b.id).name == "Neubau"


def test_create_wg(session):
    b = Building(name="Altbau")
    session.add(b)
    session.flush()
    wg = WG(building_id=b.id, name="OJ1")
    session.add(wg)
    session.flush()
    assert wg.id is not None
    assert wg.name == "OJ1"


def test_wg_requires_valid_building(session):
    with pytest.raises(IntegrityError):
        with session.begin_nested():  # savepoint — keeps outer transaction usable
            wg = WG(building_id=999999, name="Ghost")
            session.add(wg)
            session.flush()
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_models/test_building_wg.py -v
```

Expected: `ImportError`.

- [ ] **Step 3: Implement models**

```python
# cartei_db/models/building.py
from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column
from cartei_db.base import Base


class Building(Base):
    __tablename__ = "building"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String, nullable=False, unique=True)
```

```python
# cartei_db/models/wg.py
from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column
from cartei_db.base import Base


class WG(Base):
    __tablename__ = "wg"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    building_id: Mapped[int] = mapped_column(ForeignKey("building.id"), nullable=False)
    name: Mapped[str] = mapped_column(String, nullable=False)
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/test_models/test_building_wg.py -v
```

Expected: 3 PASS.

- [ ] **Step 5: Commit**

```bash
git add cartei_db/models/building.py cartei_db/models/wg.py tests/test_models/test_building_wg.py
git commit -m "feat: add Building and WG models"
```

---

### Task 5: Room model

**Files:**
- Create: `cartei_db/models/room.py`
- Create: `tests/test_models/test_room.py`

**Interfaces:**
- Consumes: `Base`, `Historized` from `cartei_db.base`; FK to `wg.id`
- Produces: `Room(id, wg_id, name, size_sqm, has_mattress, has_bed, has_table, has_closet, freifinanziert)` — historized

- [ ] **Step 1: Write failing tests**

```python
# tests/test_models/test_room.py
from decimal import Decimal
import pytest
from cartei_db.models.building import Building
from cartei_db.models.wg import WG
from cartei_db.models.room import Room
from cartei_db.base import EntityHistory


@pytest.fixture
def wg(session):
    b = Building(name="NB_Room")
    session.add(b)
    session.flush()
    w = WG(building_id=b.id, name="1.05")
    session.add(w)
    session.flush()
    return w


def test_create_room(session, wg):
    r = Room(
        wg_id=wg.id, name="1.05.3", size_sqm=Decimal("12.50"),
        has_mattress=True, has_bed=True, has_table=False,
        has_closet=True, freifinanziert=True,
    )
    session.add(r)
    session.flush()
    assert r.id is not None


def test_room_size_update_writes_history(session, wg):
    r = Room(
        wg_id=wg.id, name="1.05.1", size_sqm=Decimal("10.00"),
        has_mattress=False, has_bed=False, has_table=False,
        has_closet=False, freifinanziert=False,
    )
    session.add(r)
    session.flush()

    r.size_sqm = Decimal("11.50")
    session.flush()

    history = session.query(EntityHistory).filter_by(
        entity_type="room", entity_id=r.id
    ).one()
    assert history.snapshot["size_sqm"] == "10.00"


def test_freifinanziert_default_false(session, wg):
    r = Room(
        wg_id=wg.id, name="1.05.2", size_sqm=Decimal("9.00"),
        has_mattress=False, has_bed=False, has_table=False,
        has_closet=False, freifinanziert=False,
    )
    session.add(r)
    session.flush()
    assert session.get(Room, r.id).freifinanziert is False
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_models/test_room.py -v
```

Expected: `ImportError`.

- [ ] **Step 3: Implement Room model**

```python
# cartei_db/models/room.py
from decimal import Decimal
from sqlalchemy import Boolean, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column
from cartei_db.base import Base, Historized


class Room(Historized, Base):
    __tablename__ = "room"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    wg_id: Mapped[int] = mapped_column(ForeignKey("wg.id"), nullable=False)
    name: Mapped[str] = mapped_column(String, nullable=False)
    size_sqm: Mapped[Decimal] = mapped_column(Numeric(8, 2), nullable=False)
    has_mattress: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    has_bed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    has_table: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    has_closet: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    freifinanziert: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/test_models/test_room.py -v
```

Expected: 3 PASS.

- [ ] **Step 5: Commit**

```bash
git add cartei_db/models/room.py tests/test_models/test_room.py
git commit -m "feat: add Room model with history"
```

---

### Task 6: Tenant model

**Files:**
- Create: `cartei_db/models/tenant.py`
- Create: `tests/test_models/test_tenant.py`

**Interfaces:**
- Consumes: `Base`, `Historized` from `cartei_db.base`
- Produces: `Tenant` — historized, `__history_exclude__ = {"is_flinta"}`, self-referential FK for sublets

- [ ] **Step 1: Write failing tests**

```python
# tests/test_models/test_tenant.py
import uuid
from datetime import date
from decimal import Decimal
from cartei_db.models.tenant import Tenant
from cartei_db.base import EntityHistory


def _tenant(**overrides) -> Tenant:
    defaults = dict(
        first_name="Anna", last_name="Muster",
        email="anna@example.com", intranet_username="amuster",
        intranet_uuid=uuid.uuid4(), is_flinta=True,
        barrier_free_needed=False, mailbox_key=False,
        mailbox_list_opt_in=False, soli_miete_wunsch=Decimal("0"),
        is_sublet=False, move_in=date(2023, 9, 1),
    )
    defaults.update(overrides)
    return Tenant(**defaults)


def test_create_tenant(session):
    t = _tenant()
    session.add(t)
    session.flush()
    assert t.id is not None


def test_update_email_writes_history(session):
    t = _tenant(email="old@example.com")
    session.add(t)
    session.flush()
    t.email = "new@example.com"
    session.flush()
    history = session.query(EntityHistory).filter_by(
        entity_type="tenant", entity_id=t.id
    ).one()
    assert history.snapshot["email"] == "old@example.com"


def test_is_flinta_excluded_from_history(session):
    t = _tenant(is_flinta=True)
    session.add(t)
    session.flush()
    t.email = "changed@example.com"
    t.is_flinta = False
    session.flush()
    history = session.query(EntityHistory).filter_by(
        entity_type="tenant", entity_id=t.id
    ).one()
    assert "is_flinta" not in history.snapshot


def test_sublet_references_primary_tenant(session):
    primary = _tenant(intranet_username="primary", intranet_uuid=uuid.uuid4())
    session.add(primary)
    session.flush()
    sub = _tenant(
        intranet_username="subtenant", intranet_uuid=uuid.uuid4(),
        email="sub@example.com", is_sublet=True,
        sublet_from=date(2024, 1, 1), sublet_to=date(2024, 6, 30),
        sublet_of_tenant_id=primary.id,
    )
    session.add(sub)
    session.flush()
    assert sub.sublet_of_tenant_id == primary.id


def test_soli_miete_wunsch_can_be_negative(session):
    t = _tenant(soli_miete_wunsch=Decimal("-15.00"))
    session.add(t)
    session.flush()
    assert session.get(Tenant, t.id).soli_miete_wunsch == Decimal("-15.00")
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_models/test_tenant.py -v
```

Expected: `ImportError`.

- [ ] **Step 3: Implement Tenant model**

```python
# cartei_db/models/tenant.py
import uuid
from datetime import date
from decimal import Decimal
from typing import Optional

from sqlalchemy import Boolean, Date, ForeignKey, Integer, Numeric, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from cartei_db.base import Base, Historized


class Tenant(Historized, Base):
    __tablename__ = "tenant"
    __history_exclude__ = {"is_flinta"}

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    first_name: Mapped[str] = mapped_column(String, nullable=False)
    last_name: Mapped[str] = mapped_column(String, nullable=False)
    email: Mapped[str] = mapped_column(String, nullable=False)
    intranet_username: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    intranet_uuid: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False, unique=True)
    is_flinta: Mapped[bool] = mapped_column(Boolean, nullable=False)
    study_subject: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    apprenticeship_field: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    barrier_free_needed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    mailbox_key: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    mailbox_list_opt_in: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    soli_miete_wunsch: Mapped[Decimal] = mapped_column(
        Numeric(10, 2), nullable=False, default=Decimal("0")
    )
    is_sublet: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    sublet_from: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    sublet_to: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    sublet_of_tenant_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("tenant.id"), nullable=True
    )
    move_in: Mapped[date] = mapped_column(Date, nullable=False)
    move_out: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    comments: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    sublet_of: Mapped[Optional["Tenant"]] = relationship(
        "Tenant", remote_side="Tenant.id", foreign_keys=[sublet_of_tenant_id]
    )
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/test_models/test_tenant.py -v
```

Expected: 5 PASS.

- [ ] **Step 5: Commit**

```bash
git add cartei_db/models/tenant.py tests/test_models/test_tenant.py
git commit -m "feat: add Tenant model with history"
```

---

### Task 7: TenantRoomAssignment model

**Files:**
- Create: `cartei_db/models/tenant_room_assignment.py`
- Create: `tests/test_models/test_tenant_room_assignment.py`

**Interfaces:**
- Consumes: `Base` from `cartei_db.base`; FKs to `tenant.id` and `room.id`
- Produces: `TenantRoomAssignment(id, tenant_id, room_id, moved_in, moved_out)` — not historized (this table is the history)

- [ ] **Step 1: Write failing tests**

```python
# tests/test_models/test_tenant_room_assignment.py
import uuid
from datetime import date
from decimal import Decimal
import pytest
from cartei_db.models.building import Building
from cartei_db.models.wg import WG
from cartei_db.models.room import Room
from cartei_db.models.tenant import Tenant
from cartei_db.models.tenant_room_assignment import TenantRoomAssignment


@pytest.fixture
def tenant(session):
    t = Tenant(
        first_name="Max", last_name="Muster", email="max@example.com",
        intranet_username="mmuster_tra", intranet_uuid=uuid.uuid4(),
        is_flinta=False, barrier_free_needed=False, mailbox_key=False,
        mailbox_list_opt_in=False, soli_miete_wunsch=Decimal("0"),
        is_sublet=False, move_in=date(2023, 9, 1),
    )
    session.add(t)
    session.flush()
    return t


@pytest.fixture
def room(session):
    b = Building(name="NB_TRA")
    session.add(b)
    session.flush()
    w = WG(building_id=b.id, name="2.03")
    session.add(w)
    session.flush()
    r = Room(
        wg_id=w.id, name="2.03.1", size_sqm=Decimal("11.00"),
        has_mattress=False, has_bed=False, has_table=False,
        has_closet=False, freifinanziert=False,
    )
    session.add(r)
    session.flush()
    return r


def test_assign_tenant_to_room(session, tenant, room):
    a = TenantRoomAssignment(
        tenant_id=tenant.id, room_id=room.id, moved_in=date(2023, 9, 1)
    )
    session.add(a)
    session.flush()
    assert a.id is not None
    assert a.moved_out is None


def test_current_assignment_query(session, tenant, room):
    session.add(TenantRoomAssignment(
        tenant_id=tenant.id, room_id=room.id, moved_in=date(2023, 9, 1)
    ))
    session.flush()
    current = session.query(TenantRoomAssignment).filter(
        TenantRoomAssignment.tenant_id == tenant.id,
        TenantRoomAssignment.moved_out.is_(None),
    ).one()
    assert current.room_id == room.id


def test_move_out(session, tenant, room):
    a = TenantRoomAssignment(
        tenant_id=tenant.id, room_id=room.id, moved_in=date(2023, 9, 1)
    )
    session.add(a)
    session.flush()
    a.moved_out = date(2024, 3, 31)
    session.flush()
    assert session.get(TenantRoomAssignment, a.id).moved_out == date(2024, 3, 31)
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_models/test_tenant_room_assignment.py -v
```

Expected: `ImportError`.

- [ ] **Step 3: Implement TenantRoomAssignment**

```python
# cartei_db/models/tenant_room_assignment.py
from datetime import date
from typing import Optional
from sqlalchemy import Date, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column
from cartei_db.base import Base


class TenantRoomAssignment(Base):
    __tablename__ = "tenant_room_assignment"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    tenant_id: Mapped[int] = mapped_column(ForeignKey("tenant.id"), nullable=False)
    room_id: Mapped[int] = mapped_column(ForeignKey("room.id"), nullable=False)
    moved_in: Mapped[date] = mapped_column(Date, nullable=False)
    moved_out: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/test_models/test_tenant_room_assignment.py -v
```

Expected: 3 PASS.

- [ ] **Step 5: Commit**

```bash
git add cartei_db/models/tenant_room_assignment.py tests/test_models/test_tenant_room_assignment.py
git commit -m "feat: add TenantRoomAssignment model"
```

---

### Task 8: AG models (AGAbfrage + AGAbfrageResult)

**Files:**
- Create: `cartei_db/models/ag_abfrage.py`
- Create: `cartei_db/models/ag_abfrage_result.py`
- Create: `tests/test_models/test_ag.py`

**Interfaces:**
- Consumes: `Base`, `Historized` from `cartei_db.base`; `AGStatus` from `cartei_db.enums`; FK to `tenant.id`
- Produces:
  - `AGAbfrage(id: int, date: date, label: str | None)` — not historized
  - `AGAbfrageResult(id, abfrage_id, ag_name, tenant_id, status: AGStatus)` — historized

- [ ] **Step 1: Write failing tests**

```python
# tests/test_models/test_ag.py
import uuid
from datetime import date
from decimal import Decimal
import pytest
from cartei_db.models.ag_abfrage import AGAbfrage
from cartei_db.models.ag_abfrage_result import AGAbfrageResult
from cartei_db.models.tenant import Tenant
from cartei_db.base import EntityHistory
from cartei_db.enums import AGStatus


@pytest.fixture
def tenant(session):
    t = Tenant(
        first_name="Test", last_name="User", email="t@example.com",
        intranet_username="tuser_ag", intranet_uuid=uuid.uuid4(),
        is_flinta=False, barrier_free_needed=False, mailbox_key=False,
        mailbox_list_opt_in=False, soli_miete_wunsch=Decimal("0"),
        is_sublet=False, move_in=date(2023, 9, 1),
    )
    session.add(t)
    session.flush()
    return t


def test_create_abfrage(session):
    a = AGAbfrage(date=date(2024, 3, 1), label="Abfrage 2024-1")
    session.add(a)
    session.flush()
    assert a.id is not None


def test_create_result(session, tenant):
    abfrage = AGAbfrage(date=date(2024, 3, 1))
    session.add(abfrage)
    session.flush()
    result = AGAbfrageResult(
        abfrage_id=abfrage.id, ag_name="AG Küche",
        tenant_id=tenant.id, status=AGStatus.ACTIVE,
    )
    session.add(result)
    session.flush()
    assert result.id is not None


def test_multiple_ags_per_tenant_per_round(session, tenant):
    abfrage = AGAbfrage(date=date(2024, 3, 1))
    session.add(abfrage)
    session.flush()
    for ag in ["AG Küche", "AG Garten"]:
        session.add(AGAbfrageResult(
            abfrage_id=abfrage.id, ag_name=ag,
            tenant_id=tenant.id, status=AGStatus.ACTIVE,
        ))
    session.flush()
    results = session.query(AGAbfrageResult).filter_by(
        abfrage_id=abfrage.id, tenant_id=tenant.id
    ).all()
    assert len(results) == 2


def test_result_status_update_writes_history(session, tenant):
    abfrage = AGAbfrage(date=date(2024, 6, 1))
    session.add(abfrage)
    session.flush()
    result = AGAbfrageResult(
        abfrage_id=abfrage.id, ag_name="AG Küche",
        tenant_id=tenant.id, status=AGStatus.ACTIVE,
    )
    session.add(result)
    session.flush()
    result.status = AGStatus.NOT_ACTIVE_ENOUGH
    session.flush()
    history = session.query(EntityHistory).filter_by(
        entity_type="ag_abfrage_result", entity_id=result.id
    ).one()
    assert history.snapshot["status"] == "ACTIVE"
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_models/test_ag.py -v
```

Expected: `ImportError`.

- [ ] **Step 3: Implement AG models**

```python
# cartei_db/models/ag_abfrage.py
from datetime import date
from typing import Optional
from sqlalchemy import Date, Integer, String
from sqlalchemy.orm import Mapped, mapped_column
from cartei_db.base import Base


class AGAbfrage(Base):
    __tablename__ = "ag_abfrage"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    date: Mapped[date] = mapped_column(Date, nullable=False)
    label: Mapped[Optional[str]] = mapped_column(String, nullable=True)
```

```python
# cartei_db/models/ag_abfrage_result.py
from sqlalchemy import Enum as SAEnum, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column
from cartei_db.base import Base, Historized
from cartei_db.enums import AGStatus


class AGAbfrageResult(Historized, Base):
    __tablename__ = "ag_abfrage_result"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    abfrage_id: Mapped[int] = mapped_column(ForeignKey("ag_abfrage.id"), nullable=False)
    ag_name: Mapped[str] = mapped_column(String, nullable=False)
    tenant_id: Mapped[int] = mapped_column(ForeignKey("tenant.id"), nullable=False)
    status: Mapped[AGStatus] = mapped_column(SAEnum(AGStatus), nullable=False)
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/test_models/test_ag.py -v
```

Expected: 4 PASS.

- [ ] **Step 5: Commit**

```bash
git add cartei_db/models/ag_abfrage.py cartei_db/models/ag_abfrage_result.py tests/test_models/test_ag.py
git commit -m "feat: add AGAbfrage and AGAbfrageResult models"
```

---

### Task 9: EnrollmentProof model

**Files:**
- Create: `cartei_db/models/enrollment_proof.py`
- Create: `tests/test_models/test_enrollment_proof.py`

**Interfaces:**
- Consumes: `Base` from `cartei_db.base`; `EnrollmentType` from `cartei_db.enums`; FK to `tenant.id`
- Produces: `EnrollmentProof(id, tenant_id, enrollment_type, enrollment_name, file_data, file_name, submitted_at, valid_until)` — not historized; multiple records accumulate, consumers query latest by `submitted_at DESC`

- [ ] **Step 1: Write failing tests**

```python
# tests/test_models/test_enrollment_proof.py
import uuid
from datetime import date, datetime, timezone
from decimal import Decimal
import pytest
from cartei_db.models.enrollment_proof import EnrollmentProof
from cartei_db.models.tenant import Tenant
from cartei_db.enums import EnrollmentType


@pytest.fixture
def tenant(session):
    t = Tenant(
        first_name="Lea", last_name="Test", email="lea@example.com",
        intranet_username="ltest_ep", intranet_uuid=uuid.uuid4(),
        is_flinta=True, barrier_free_needed=False, mailbox_key=False,
        mailbox_list_opt_in=False, soli_miete_wunsch=Decimal("0"),
        is_sublet=False, move_in=date(2023, 9, 1),
    )
    session.add(t)
    session.flush()
    return t


def test_store_study_proof(session, tenant):
    proof = EnrollmentProof(
        tenant_id=tenant.id,
        enrollment_type=EnrollmentType.STUDY,
        enrollment_name="Informatik B.Sc.",
        file_data=b"%PDF-1.4 fake content",
        file_name="immatrikulation.pdf",
        submitted_at=datetime(2024, 3, 1, 10, 0, tzinfo=timezone.utc),
        valid_until=date(2024, 9, 1),
    )
    session.add(proof)
    session.flush()
    fetched = session.get(EnrollmentProof, proof.id)
    assert fetched.file_data == b"%PDF-1.4 fake content"
    assert fetched.enrollment_name == "Informatik B.Sc."


def test_latest_proof_query(session, tenant):
    for month in [3, 9]:
        session.add(EnrollmentProof(
            tenant_id=tenant.id,
            enrollment_type=EnrollmentType.STUDY,
            enrollment_name="Informatik B.Sc.",
            file_data=b"pdf",
            file_name=f"proof_{month}.pdf",
            submitted_at=datetime(2024, month, 1, tzinfo=timezone.utc),
            valid_until=date(2024, 9, 1) if month == 3 else date(2025, 3, 1),
        ))
    session.flush()
    latest = (
        session.query(EnrollmentProof)
        .filter_by(tenant_id=tenant.id)
        .order_by(EnrollmentProof.submitted_at.desc())
        .first()
    )
    assert latest.submitted_at.month == 9


def test_apprenticeship_proof(session, tenant):
    proof = EnrollmentProof(
        tenant_id=tenant.id,
        enrollment_type=EnrollmentType.APPRENTICESHIP,
        enrollment_name="Tischler",
        file_data=b"contract bytes",
        file_name="ausbildungsvertrag.pdf",
        submitted_at=datetime(2024, 3, 1, tzinfo=timezone.utc),
        valid_until=date(2024, 9, 1),
    )
    session.add(proof)
    session.flush()
    assert proof.enrollment_type == EnrollmentType.APPRENTICESHIP
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_models/test_enrollment_proof.py -v
```

Expected: `ImportError`.

- [ ] **Step 3: Implement EnrollmentProof**

```python
# cartei_db/models/enrollment_proof.py
from datetime import date, datetime
from sqlalchemy import Date, DateTime, Enum as SAEnum, ForeignKey, Integer, LargeBinary, String
from sqlalchemy.orm import Mapped, mapped_column
from cartei_db.base import Base
from cartei_db.enums import EnrollmentType


class EnrollmentProof(Base):
    __tablename__ = "enrollment_proof"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    tenant_id: Mapped[int] = mapped_column(ForeignKey("tenant.id"), nullable=False)
    enrollment_type: Mapped[EnrollmentType] = mapped_column(
        SAEnum(EnrollmentType), nullable=False
    )
    enrollment_name: Mapped[str] = mapped_column(String, nullable=False)
    file_data: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
    file_name: Mapped[str] = mapped_column(String, nullable=False)
    submitted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    valid_until: Mapped[date] = mapped_column(Date, nullable=False)
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/test_models/test_enrollment_proof.py -v
```

Expected: 3 PASS.

- [ ] **Step 5: Commit**

```bash
git add cartei_db/models/enrollment_proof.py tests/test_models/test_enrollment_proof.py
git commit -m "feat: add EnrollmentProof model"
```

---

### Task 10: models/__init__.py + Alembic setup + initial migration

**Files:**
- Create: `cartei_db/models/__init__.py`
- Create: `alembic.ini` (via `alembic init`, then edit)
- Create: `migrations/env.py` (replace generated file)

**Interfaces:**
- Consumes: all 8 model classes from previous tasks
- Produces: `alembic upgrade head` creates all tables on a fresh database

- [ ] **Step 1: Create cartei_db/models/__init__.py**

```python
# cartei_db/models/__init__.py
from cartei_db.models.building import Building
from cartei_db.models.wg import WG
from cartei_db.models.room import Room
from cartei_db.models.tenant import Tenant
from cartei_db.models.tenant_room_assignment import TenantRoomAssignment
from cartei_db.models.ag_abfrage import AGAbfrage
from cartei_db.models.ag_abfrage_result import AGAbfrageResult
from cartei_db.models.enrollment_proof import EnrollmentProof

__all__ = [
    "Building", "WG", "Room", "Tenant", "TenantRoomAssignment",
    "AGAbfrage", "AGAbfrageResult", "EnrollmentProof",
]
```

- [ ] **Step 2: Initialize Alembic**

```bash
alembic init migrations
```

- [ ] **Step 3: Edit alembic.ini — disable hardcoded URL**

Find and comment out the `sqlalchemy.url` line (URL is set programmatically in `env.py`):

```ini
# sqlalchemy.url = driver://user:pass@localhost/dbname
```

- [ ] **Step 4: Replace migrations/env.py**

```python
# migrations/env.py
import os
from alembic import context
from sqlalchemy import engine_from_config, pool

from cartei_db.base import Base
import cartei_db.models  # noqa: F401 — registers all models in Base.metadata

config = context.config
config.set_main_option("sqlalchemy.url", os.environ["DATABASE_URL"])
target_metadata = Base.metadata


def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


run_migrations_online()
```

- [ ] **Step 5: Generate initial migration**

```bash
export DATABASE_URL=postgresql://postgres:postgres@localhost/cartei_test
alembic revision --autogenerate -m "initial schema"
```

Open the generated file in `migrations/versions/`. Verify it has `create_table` calls for:
`entity_history`, `building`, `wg`, `room`, `tenant`, `tenant_room_assignment`, `ag_abfrage`, `ag_abfrage_result`, `enrollment_proof`.

If `_test_thing` appears (it should not — `env.py` only imports production models), remove those create/drop operations.

- [ ] **Step 6: Apply migration to a fresh database and verify**

```bash
# Use a separate fresh DB to test the migration independently of the test DB
createdb cartei_fresh  # or: psql -c "CREATE DATABASE cartei_fresh;"
export DATABASE_URL=postgresql://postgres:postgres@localhost/cartei_fresh
alembic upgrade head
psql $DATABASE_URL -c "\dt"
```

Expected tables: `ag_abfrage`, `ag_abfrage_result`, `alembic_version`, `building`, `enrollment_proof`, `entity_history`, `room`, `tenant`, `tenant_room_assignment`, `wg`.

- [ ] **Step 7: Run the full test suite**

```bash
export DATABASE_URL=postgresql://postgres:postgres@localhost/cartei_test
pytest -v
```

Expected: all tests PASS (should be ~27 tests across all files).

- [ ] **Step 8: Commit**

```bash
git add cartei_db/models/__init__.py alembic.ini migrations/
git commit -m "feat: Alembic setup and initial migration"
```
