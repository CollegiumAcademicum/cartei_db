# CArtei DB — Design Spec

**Date:** 2026-08-04  
**Project:** cartei_db  
**Purpose:** Shared data layer (PostgreSQL + SQLAlchemy) for CArtei, the tenant management system of Collegium Academicum. All microservices and macroservices depend on this library for their data models and migrations.

---

## 1. Architecture

### What this package is

A Python library installed by consuming services. It owns:
- SQLAlchemy models (table definitions)
- Alembic migration scripts
- The `Historized` mixin and `entity_history` table

It does **not** run a server, expose an API, or manage sessions. Consuming services import models and supply their own engine/session.

### Package layout

```
cartei_db/
├── base.py           # DeclarativeBase, Historized mixin, entity_history table
├── enums.py          # AGStatus, ChangeSource, EnrollmentType
└── models/
    ├── building.py
    ├── wg.py
    ├── room.py
    ├── tenant.py
    ├── tenant_room_assignment.py
    ├── ag_abfrage.py
    ├── ag_abfrage_result.py
    └── enrollment_proof.py

migrations/           # Alembic (project root, not inside package)
    versions/
    env.py            # imports cartei_db.models.*, reads DATABASE_URL
alembic.ini
```

### Consumption pattern

```python
from cartei_db.models.tenant import Tenant
from cartei_db.models.room import Room
# Use with consuming service's own engine/session
```

Migrations are run once via a dedicated one-shot container — not by every consuming service.

### Tech stack

- **Python 3.14**
- **PostgreSQL** — primary database
- **SQLAlchemy** — ORM
- **Alembic** — migrations
- **Fedora CoreOS + Podman + Quadlets** — deployment target

---

## 2. Enums

Defined in `enums.py`:

| Enum | Values |
|---|---|
| `AGStatus` | `ACTIVE`, `NOT_ACTIVE_ENOUGH`, `CONTACTED`, `INACTIVE` |
| `ChangeSource` | `HUMAN`, `SERVICE` |
| `EnrollmentType` | `STUDY`, `APPRENTICESHIP` |

---

## 3. Data Model

### Building
Static — not historized.

| field | type | notes |
|---|---|---|
| id | int PK | |
| name | str | "Neubau", "Altbau" |

### WG
Static — not historized.

| field | type | notes |
|---|---|---|
| id | int PK | |
| building_id | FK → Building | |
| name | str | "1.05", "OJ1", "SWB3", "FFW2" |

Room naming in Neubau follows `floor.wg.room` (e.g. `1.05.3`): floor 0–3, WG 1–13, room 1–4. Altbau WGs (OJ1–4, SWB1–6, FFW1–2) have varying room counts.

### Room
Historized — size and furnishings are mutable.

| field | type | notes |
|---|---|---|
| id | int PK | |
| wg_id | FK → WG | |
| name | str | "1.05.3" or room number in Altbau |
| size_sqm | Decimal | mutable |
| has_mattress | bool | |
| has_bed | bool | |
| has_table | bool | |
| has_closet | bool | |
| freifinanziert | bool | true = privately financed (not Sozialwohnung) |

### Tenant
Historized. `__history_exclude__ = {"is_flinta"}`.

| field | type | notes |
|---|---|---|
| id | int PK | |
| first_name | str | |
| last_name | str | |
| email | str | |
| intranet_username | str, unique | LDAP username |
| intranet_uuid | UUID, unique | LDAP UUID |
| is_flinta | bool | excluded from history |
| study_subject | str, nullable | |
| apprenticeship_field | str, nullable | |
| barrier_free_needed | bool | |
| mailbox_key | bool | |
| mailbox_list_opt_in | bool | |
| soli_miete_wunsch | Decimal | + = paying more, − = receiving |
| is_sublet | bool | |
| sublet_from | date, nullable | |
| sublet_to | date, nullable | |
| sublet_of_tenant_id | FK → Tenant, nullable | whose sublet they are |
| move_in | date | overall CA tenure start |
| move_out | date, nullable | NULL = currently living there |
| comments | text, nullable | |

### TenantRoomAssignment
Not historized — this table *is* the room history.

| field | type | notes |
|---|---|---|
| id | int PK | |
| tenant_id | FK → Tenant | |
| room_id | FK → Room | |
| moved_in | date | |
| moved_out | date, nullable | NULL = current assignment |

### AGAbfrage
Immutable once created. ~8 rounds per year. Not historized.

| field | type | notes |
|---|---|---|
| id | int PK | |
| date | date | |
| label | str, nullable | |

### AGAbfrageResult
Historized — results can be corrected after submission. AG membership lives in LDAP; this table only stores the reported activity status per round.

| field | type | notes |
|---|---|---|
| id | int PK | |
| abfrage_id | FK → AGAbfrage | |
| ag_name | str | AG identifier from LDAP |
| tenant_id | FK → Tenant | |
| status | AGStatus enum | |

A tenant can appear multiple times per round (once per AG they belong to).

### EnrollmentProof
Not historized — multiple records accumulate naturally; consumers take the latest by `submitted_at`.

| field | type | notes |
|---|---|---|
| id | int PK | |
| tenant_id | FK → Tenant | |
| enrollment_type | EnrollmentType enum | |
| enrollment_name | str | e.g. "Informatik B.Sc.", "Tischler" |
| file_data | bytea | actual document |
| file_name | str | original filename |
| submitted_at | datetime (UTC) | |
| valid_until | date | ~6 months validity |

---

## 4. History Mechanism

### entity_history table

| field | type | notes |
|---|---|---|
| id | int PK | |
| entity_type | str | e.g. "tenant", "room" |
| entity_id | int | |
| snapshot | JSONB | full row state *before* the change |
| changed_at | datetime (UTC) | |
| changed_by | str | intranet username or service name |
| change_source | ChangeSource enum | |

### Historized mixin

Applied to: `Tenant`, `Room`, `AGAbfrageResult`.

```python
class Historized:
    __history_exclude__: set[str] = set()

    @classmethod
    def __declare_last__(cls):
        listen(cls, "before_update", _capture_snapshot)
        listen(cls, "before_delete", _capture_snapshot)
```

On every update or delete, the listener serializes the current row (excluding `__history_exclude__` fields) into JSONB and writes to `entity_history`. The consuming service injects `changed_by` and `change_source` via a `contextvars.ContextVar` (Python stdlib) before committing. The listener reads these vars at write time.

### Point-in-time query pattern

```python
session.query(EntityHistory).filter(
    EntityHistory.entity_type == "tenant",
    EntityHistory.entity_id == tenant_id,
    EntityHistory.changed_at <= target_datetime,
).order_by(EntityHistory.changed_at.desc()).first()
```

---

## 5. Migrations

Alembic with autogenerate. `env.py` imports all models from `cartei_db.models` and reads the database URL from `DATABASE_URL` env var.

### Schema change workflow

```bash
alembic revision --autogenerate -m "description"
# Review generated file
alembic upgrade head
```

### Running in Podman/Quadlets

A one-shot `.container` Quadlet unit runs `alembic upgrade head` before any consuming service starts:

```ini
# cartei-migrate.container
[Container]
Image=cartei-db:latest
Exec=alembic upgrade head
Environment=DATABASE_URL=postgresql://...

[Service]
Type=oneshot
RemainAfterExit=yes
```

Consuming service units declare `After=cartei-migrate.service` and `Requires=cartei-migrate.service`.

---

## 6. Future Extensions (out of scope now)

- **Pricing / Nebenkosten:** Additive — `RoomRent` (temporal) and `Nebenkostenabrechnung` tables. `TenantRoomAssignment` already provides the "who lived where when" query needed for billing calculations.
- **Soli Miete min/max enforcement:** `CHECK` constraint via Alembic migration once limits are decided.
