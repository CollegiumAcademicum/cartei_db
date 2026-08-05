# CArtei App — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the CArtei Django web app for AG engagement management, on top of the `cartei_db` shared schema.

**Architecture:** Two-repo setup: `cartei_db` owns the PostgreSQL schema (Alembic migrations), and the new `cartei` Django app uses `managed=False` models that mirror those tables without touching them. Auth is handled by `django-auth-ldap` backed by FreeIPA, with LDAP group membership synced to Django groups on every login. The `cartei_deployment` repo already has a placeholder for the `app` container.

**Tech Stack:** Python 3.14, Django ≥ 5.0, django-auth-ldap ≥ 4.8, python-ldap, psycopg (psycopg3), gunicorn, whitenoise, pytest-django, uv.

## Global Constraints

- Python 3.14, Django ≥ 5.0
- `managed = False` on all domain models — Alembic owns the schema
- All LDAP config from environment variables — no hardcoded values
- `LDAP_REQUIRE_GROUP` (`confidentiality_clearance`) is the sole login gate — no separate residents group
- `CARTEI_ADMIN_GROUP` defaults to `ag.it`; can be changed to a dedicated group later via env var
- AG names stored as short CN (e.g. `ag.kueche`), not full LDAP DN
- No CSS framework — minimal inline styles in base.html for MVP
- No JavaScript — all interactions are plain HTML form posts

## File Map

### In `cartei_db` repo (`/Users/philipp/git-repos/cartei_db`)

| Action | File | Responsibility |
|---|---|---|
| Modify | `cartei_db/models/ag_abfrage.py` | Add `ends_at`, `grace_ends_at` |
| Modify | `cartei_db/models/ag_abfrage_result.py` | Add `note` |
| Modify | `cartei_db/models/tenant.py` | Make `move_in` nullable; add `server_default='false'` to `is_flinta` |
| Create | `cartei_db/models/cluster_note.py` | New ClusterNote model |
| Modify | `cartei_db/models/__init__.py` | Export `ClusterNote` |
| Create | `migrations/versions/<hash>_engagement_and_cluster_note.py` | Alembic migration |
| Modify | `tests/test_models/test_ag.py` | Update fixtures for new required fields; add ClusterNote test |

### New `cartei` repo (`/Users/philipp/git-repos/cartei`)

| Action | File | Responsibility |
|---|---|---|
| Create | `pyproject.toml` | Project metadata and deps |
| Create | `.python-version` | Pin 3.14 |
| Create | `.gitignore` | Standard Python + Django ignores |
| Create | `.env.example` | All env vars documented |
| Create | `Dockerfile` | Production image (libldap-dev, uv) |
| Create | `gunicorn.conf.py` | WSGI server config |
| Create | `manage.py` | Django entrypoint |
| Create | `cartei/__init__.py` | Empty |
| Create | `cartei/settings.py` | Django + LDAP config from env vars |
| Create | `cartei/settings_test.py` | SQLite, no LDAP, test-safe |
| Create | `cartei/urls.py` | Root URL conf (login/logout + app.urls) |
| Create | `cartei/wsgi.py` | WSGI application |
| Create | `app/__init__.py` | Empty |
| Create | `app/auth.py` | `CustomLDAPBackend`: group sync + auto-create Tenant |
| Create | `app/decorators.py` | `require_group(*groups)` |
| Create | `app/models.py` | `managed=False` mirrors + `AGStatus` TextChoices |
| Create | `app/ldap_utils.py` | `get_clearance_members()`, `get_ag_members(ag_name)` |
| Create | `app/urls.py` | All app URL patterns |
| Create | `app/views/__init__.py` | Empty |
| Create | `app/views/admin_views.py` | `sync_from_ldap` bulk sync view |
| Create | `app/views/abfragen.py` | All AG engagement views |
| Create | `app/templates/app/base.html` | Base layout with nav |
| Create | `app/templates/app/login.html` | Login form |
| Create | `app/templates/app/abfragen/list.html` | Abfragen list |
| Create | `app/templates/app/abfragen/new.html` | Create new Abfrage |
| Create | `app/templates/app/abfragen/detail.html` | Cluster/admin overview |
| Create | `app/templates/app/abfragen/ag_edit.html` | AG member evaluation form |
| Create | `app/templates/app/abfragen/tenants.html` | Per-tenant view with cluster notes |
| Create | `tests/__init__.py` | Empty |
| Create | `tests/conftest.py` | DB setup: override managed=True for domain models |
| Create | `tests/test_auth.py` | `_dn_to_cn`, `_sync_groups`, `_ensure_tenant` |
| Create | `tests/test_models.py` | `AGAbfrage.state`, `can_ag_edit` |
| Create | `tests/test_views_abfragen.py` | Access control + form submission |
| Create | `tests/test_views_admin.py` | Sync view access + behavior (mocked LDAP) |

---

## Task 0: cartei_db Schema Changes

**Files:**
- Modify: `cartei_db/models/ag_abfrage.py`
- Modify: `cartei_db/models/ag_abfrage_result.py`
- Modify: `cartei_db/models/tenant.py`
- Create: `cartei_db/models/cluster_note.py`
- Modify: `cartei_db/models/__init__.py`
- Create: `migrations/versions/<hash>_engagement_and_cluster_note.py`
- Modify: `tests/test_models/test_ag.py`

**Interfaces:**
- Produces: `AGAbfrage.ends_at: date`, `AGAbfrage.grace_ends_at: date`, `AGAbfrageResult.note: Optional[str]`, `ClusterNote` model, `Tenant.move_in` nullable, `Tenant.is_flinta` server_default='false'

- [ ] **Step 1: Update AGAbfrage model**

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
    ends_at: Mapped[date] = mapped_column(Date, nullable=False)
    grace_ends_at: Mapped[date] = mapped_column(Date, nullable=False)
```

- [ ] **Step 2: Update AGAbfrageResult model**

```python
# cartei_db/models/ag_abfrage_result.py
from typing import Optional
from sqlalchemy import Enum as SAEnum, ForeignKey, Integer, String, Text
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
    note: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
```

- [ ] **Step 3: Update Tenant model (two changes)**

In `cartei_db/models/tenant.py`:

Change line 26 from:
```python
    is_flinta: Mapped[bool] = mapped_column(Boolean, nullable=False)
```
To:
```python
    is_flinta: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false")
```

Change line 44 from:
```python
    move_in: Mapped[date] = mapped_column(Date, nullable=False)
```
To:
```python
    move_in: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
```

Also add `Optional` to the existing `from typing import Optional` import (already present on that file).

- [ ] **Step 4: Create ClusterNote model**

```python
# cartei_db/models/cluster_note.py
from datetime import datetime
from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from cartei_db.base import Base


class ClusterNote(Base):
    __tablename__ = "cluster_note"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    tenant_id: Mapped[int] = mapped_column(ForeignKey("tenant.id"), nullable=False)
    abfrage_id: Mapped[int] = mapped_column(ForeignKey("ag_abfrage.id"), nullable=False)
    note: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_by: Mapped[str] = mapped_column(String, nullable=False)
```

- [ ] **Step 5: Export ClusterNote from models package**

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
from cartei_db.models.cluster_note import ClusterNote

__all__ = [
    "Building", "WG", "Room", "Tenant", "TenantRoomAssignment",
    "AGAbfrage", "AGAbfrageResult", "EnrollmentProof", "ClusterNote",
]
```

- [ ] **Step 6: Write the failing tests**

```python
# tests/test_models/test_ag.py  (replace entire file)
import uuid
from datetime import date, datetime, timezone
from decimal import Decimal
import pytest
from cartei_db.models.ag_abfrage import AGAbfrage
from cartei_db.models.ag_abfrage_result import AGAbfrageResult
from cartei_db.models.cluster_note import ClusterNote
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


@pytest.fixture
def abfrage(session):
    a = AGAbfrage(
        date=date(2024, 3, 1),
        label="Abfrage 2024-1",
        ends_at=date(2024, 3, 31),
        grace_ends_at=date(2024, 4, 7),
    )
    session.add(a)
    session.flush()
    return a


def test_create_abfrage(session, abfrage):
    assert abfrage.id is not None
    assert abfrage.ends_at == date(2024, 3, 31)
    assert abfrage.grace_ends_at == date(2024, 4, 7)


def test_create_result(session, tenant, abfrage):
    result = AGAbfrageResult(
        abfrage_id=abfrage.id, ag_name="ag.kueche",
        tenant_id=tenant.id, status=AGStatus.ACTIVE,
    )
    session.add(result)
    session.flush()
    assert result.id is not None
    assert result.note is None


def test_result_with_note(session, tenant, abfrage):
    result = AGAbfrageResult(
        abfrage_id=abfrage.id, ag_name="ag.kueche",
        tenant_id=tenant.id, status=AGStatus.ACTIVE,
        note="Very engaged this round",
    )
    session.add(result)
    session.flush()
    assert result.note == "Very engaged this round"


def test_multiple_ags_per_tenant_per_round(session, tenant, abfrage):
    for ag in ["ag.kueche", "ag.garten"]:
        session.add(AGAbfrageResult(
            abfrage_id=abfrage.id, ag_name=ag,
            tenant_id=tenant.id, status=AGStatus.ACTIVE,
        ))
    session.flush()
    results = session.query(AGAbfrageResult).filter_by(
        abfrage_id=abfrage.id, tenant_id=tenant.id
    ).all()
    assert len(results) == 2


def test_result_status_update_writes_history(session, tenant, abfrage):
    result = AGAbfrageResult(
        abfrage_id=abfrage.id, ag_name="ag.kueche",
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


def test_create_cluster_note(session, tenant, abfrage):
    note = ClusterNote(
        tenant_id=tenant.id,
        abfrage_id=abfrage.id,
        note="Internal observation",
        created_at=datetime(2024, 3, 15, 10, 0, 0, tzinfo=timezone.utc),
        created_by="clusteruser",
    )
    session.add(note)
    session.flush()
    assert note.id is not None


def test_tenant_move_in_nullable(session):
    t = Tenant(
        first_name="New", last_name="Person", email="np@example.com",
        intranet_username="newperson", intranet_uuid=uuid.uuid4(),
        is_flinta=False, barrier_free_needed=False, mailbox_key=False,
        mailbox_list_opt_in=False, soli_miete_wunsch=Decimal("0"),
        is_sublet=False,
    )
    session.add(t)
    session.flush()
    assert t.id is not None
    assert t.move_in is None
```

- [ ] **Step 7: Run failing tests**

```bash
cd /Users/philipp/git-repos/cartei_db
uv run pytest tests/test_models/test_ag.py -v
```

Expected: most tests FAIL (`column ends_at of relation ag_abfrage does not exist`, `column note of relation ag_abfrage_result does not exist`, etc.)

- [ ] **Step 8: Generate and write the Alembic migration**

Run autogenerate to get a skeleton:
```bash
cd /Users/philipp/git-repos/cartei_db
uv run alembic revision --autogenerate -m "engagement_and_cluster_note"
```

Open the generated file in `migrations/versions/` and replace its `upgrade()` and `downgrade()` with:

```python
import sqlalchemy as sa
from alembic import op


def upgrade() -> None:
    # ag_abfrage: add ends_at and grace_ends_at (NOT NULL, temp default covers existing rows)
    op.add_column("ag_abfrage", sa.Column("ends_at", sa.Date(), nullable=False,
                  server_default=sa.text("CURRENT_DATE")))
    op.add_column("ag_abfrage", sa.Column("grace_ends_at", sa.Date(), nullable=False,
                  server_default=sa.text("CURRENT_DATE + INTERVAL '7 days'")))
    op.alter_column("ag_abfrage", "ends_at", server_default=None)
    op.alter_column("ag_abfrage", "grace_ends_at", server_default=None)

    # ag_abfrage_result: add optional note
    op.add_column("ag_abfrage_result", sa.Column("note", sa.Text(), nullable=True))

    # tenant: make move_in nullable; add server_default to is_flinta
    op.alter_column("tenant", "move_in", nullable=True,
                    existing_type=sa.Date())
    op.alter_column("tenant", "is_flinta", server_default=sa.text("false"),
                    existing_type=sa.Boolean(), existing_nullable=False)

    # cluster_note: new table
    op.create_table(
        "cluster_note",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("tenant_id", sa.Integer(), sa.ForeignKey("tenant.id"), nullable=False),
        sa.Column("abfrage_id", sa.Integer(), sa.ForeignKey("ag_abfrage.id"), nullable=False),
        sa.Column("note", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_by", sa.String(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("cluster_note")
    op.alter_column("tenant", "is_flinta", server_default=None,
                    existing_type=sa.Boolean(), existing_nullable=False)
    op.alter_column("tenant", "move_in", nullable=False, existing_type=sa.Date())
    op.drop_column("ag_abfrage_result", "note")
    op.drop_column("ag_abfrage", "grace_ends_at")
    op.drop_column("ag_abfrage", "ends_at")
```

- [ ] **Step 9: Apply the migration**

```bash
cd /Users/philipp/git-repos/cartei_db
uv run alembic upgrade head
```

Expected: migration runs without errors.

- [ ] **Step 10: Run tests — verify they pass**

```bash
uv run pytest tests/test_models/test_ag.py -v
```

Expected: all tests PASS.

- [ ] **Step 11: Run the full test suite**

```bash
uv run pytest -v
```

Expected: all tests PASS. Fix any regressions before proceeding.

- [ ] **Step 12: Commit**

```bash
cd /Users/philipp/git-repos/cartei_db
git add cartei_db/models/ag_abfrage.py \
        cartei_db/models/ag_abfrage_result.py \
        cartei_db/models/tenant.py \
        cartei_db/models/cluster_note.py \
        cartei_db/models/__init__.py \
        migrations/versions/ \
        tests/test_models/test_ag.py
git commit -m "feat: add engagement fields, ClusterNote, nullable move_in"
```

---

## Task 1: New `cartei` Repo — Scaffolding and Settings

**Files:**
- Create: `pyproject.toml`, `.python-version`, `.gitignore`, `.env.example`, `Dockerfile`, `gunicorn.conf.py`, `manage.py`, `cartei/__init__.py`, `cartei/settings.py`, `cartei/settings_test.py`, `cartei/urls.py`, `cartei/wsgi.py`, `app/__init__.py`, `app/views/__init__.py`, `tests/__init__.py`

**Interfaces:**
- Produces: Django project runnable via `uv run python manage.py check`; pytest collects with `DJANGO_SETTINGS_MODULE=cartei.settings_test`

- [ ] **Step 1: Initialize repo**

```bash
mkdir /Users/philipp/git-repos/cartei
cd /Users/philipp/git-repos/cartei
git init
git remote add origin git@github.com:CollegiumAcademicum/cartei.git
```

- [ ] **Step 2: Create `pyproject.toml`**

```toml
[project]
name = "cartei"
version = "0.1.0"
description = "CArtei tenant management system"
requires-python = ">=3.14"
dependencies = [
    "django>=5.0",
    "django-auth-ldap>=4.8",
    "psycopg[binary]>=3.0",
    "gunicorn>=22.0",
    "python-dotenv>=1.0",
    "whitenoise>=6.0",
]

[dependency-groups]
dev = [
    "pytest>=8.0",
    "pytest-django>=4.9",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["."]

[tool.pytest.ini_options]
pythonpath = ["."]
testpaths = ["tests"]
DJANGO_SETTINGS_MODULE = "cartei.settings_test"
```

- [ ] **Step 3: Create `.python-version`**

```
3.14
```

- [ ] **Step 4: Create `.gitignore`**

```gitignore
__pycache__/
*.pyc
*.pyo
.env
.venv/
staticfiles/
data/
*.sqlite3
uv.lock
.idea/
```

- [ ] **Step 5: Install dependencies**

```bash
cd /Users/philipp/git-repos/cartei
uv sync
```

- [ ] **Step 6: Create `manage.py`**

```python
#!/usr/bin/env python
import os
import sys

if __name__ == "__main__":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "cartei.settings")
    from django.core.management import execute_from_command_line
    execute_from_command_line(sys.argv)
```

- [ ] **Step 7: Create `cartei/__init__.py`** — empty file

- [ ] **Step 8: Create `cartei/settings.py`**

```python
import os
from pathlib import Path
from urllib.parse import urlparse

from django.core.exceptions import ImproperlyConfigured
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env", override=False)

_INSECURE_KEY = "insecure-dev-key-do-not-use-in-production"
SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", _INSECURE_KEY)
DEBUG = os.environ.get("DEBUG", "false").lower() == "true"

if not DEBUG and SECRET_KEY == _INSECURE_KEY:
    raise ImproperlyConfigured("DJANGO_SECRET_KEY must be set in production.")

ALLOWED_HOSTS = os.environ.get("ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")

INSTALLED_APPS = [
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "app",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "cartei.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    }
]

WSGI_APPLICATION = "cartei.wsgi.application"

_db_url = urlparse(os.environ.get("DATABASE_URL", "postgresql://localhost/cartei"))
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": _db_url.path.lstrip("/"),
        "USER": _db_url.username or "",
        "PASSWORD": _db_url.password or "",
        "HOST": _db_url.hostname or "localhost",
        "PORT": str(_db_url.port or 5432),
    }
}

LANGUAGE_CODE = "de-de"
TIME_ZONE = "Europe/Berlin"
USE_I18N = True
USE_TZ = True
STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

LOGIN_URL = "/login/"
LOGIN_REDIRECT_URL = "/abfragen/"
LOGOUT_REDIRECT_URL = "/login/"

# LDAP — skipped gracefully if python-ldap not installed
try:
    import ldap
    from django_auth_ldap.config import LDAPSearch

    AUTH_LDAP_SERVER_URI = os.environ.get("LDAP_SERVER_URI", "ldap://localhost")
    AUTH_LDAP_BIND_DN = os.environ.get("LDAP_BIND_DN", "")
    AUTH_LDAP_BIND_PASSWORD = os.environ.get("LDAP_BIND_PASSWORD", "")
    AUTH_LDAP_USER_SEARCH = LDAPSearch(
        os.environ.get("LDAP_USER_SEARCH_BASE", "dc=example,dc=com"),
        ldap.SCOPE_SUBTREE,
        "(uid=%(user)s)",
    )
    AUTH_LDAP_USER_ATTR_MAP = {
        "first_name": "givenName",
        "last_name": "sn",
        "email": "mail",
    }
    AUTH_LDAP_REQUIRE_GROUP = os.environ.get("LDAP_REQUIRE_GROUP", "")
    AUTH_LDAP_GLOBAL_OPTIONS = {ldap.OPT_REFERRALS: 0}
    _ca_cert = os.environ.get("LDAP_CA_CERT_PATH", "")
    if _ca_cert:
        try:
            ldap.set_option(ldap.OPT_X_TLS_CACERTFILE, _ca_cert)
            AUTH_LDAP_GLOBAL_OPTIONS[ldap.OPT_X_TLS_CACERTFILE] = _ca_cert
            AUTH_LDAP_GLOBAL_OPTIONS[ldap.OPT_X_TLS_REQUIRE_CERT] = ldap.OPT_X_TLS_DEMAND
        except ValueError:
            # macOS Secure Transport does not support OPT_X_TLS_CACERTFILE
            AUTH_LDAP_GLOBAL_OPTIONS[ldap.OPT_X_TLS_REQUIRE_CERT] = ldap.OPT_X_TLS_NEVER
            AUTH_LDAP_GLOBAL_OPTIONS[ldap.OPT_X_TLS_NEWCTX] = 0

    AUTHENTICATION_BACKENDS = [
        "app.auth.CustomLDAPBackend",
        "django.contrib.auth.backends.ModelBackend",
    ]
except ImportError:
    AUTHENTICATION_BACKENDS = [
        "django.contrib.auth.backends.ModelBackend",
    ]

CARTEI_ADMIN_GROUP = os.environ.get(
    "CARTEI_ADMIN_GROUP",
    "cn=ag.it,cn=groups,cn=accounts,dc=intranet,dc=ca-hd,dc=de",
)
CARTEI_CLUSTER_GROUP = os.environ.get(
    "CARTEI_CLUSTER_GROUP",
    "cn=gr.cluster,cn=groups,cn=accounts,dc=intranet,dc=ca-hd,dc=de",
)
LDAP_USER_SEARCH_BASE = os.environ.get(
    "LDAP_USER_SEARCH_BASE",
    "cn=users,cn=accounts,dc=intranet,dc=ca-hd,dc=de",
)
LDAP_GROUPS_BASE = os.environ.get(
    "LDAP_GROUPS_BASE",
    "cn=groups,cn=accounts,dc=intranet,dc=ca-hd,dc=de",
)
LDAP_REQUIRE_GROUP = os.environ.get("LDAP_REQUIRE_GROUP", "")

USE_X_FORWARDED_HOST = True
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_SSL_REDIRECT = os.environ.get("SECURE_SSL_REDIRECT", "false").lower() == "true"
_https = os.environ.get("HTTPS_ENABLED", "false").lower() == "true"
SESSION_COOKIE_SECURE = _https
CSRF_COOKIE_SECURE = _https
_csrf_origins = os.environ.get("CSRF_TRUSTED_ORIGINS", "")
CSRF_TRUSTED_ORIGINS = [o.strip() for o in _csrf_origins.split(",") if o.strip()]
SECURE_HSTS_SECONDS = int(os.environ.get("SECURE_HSTS_SECONDS", "0"))
SECURE_HSTS_INCLUDE_SUBDOMAINS = SECURE_HSTS_SECONDS > 0
SECURE_HSTS_PRELOAD = SECURE_HSTS_SECONDS > 0
SECURE_REFERRER_POLICY = "same-origin"

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {"console": {"class": "logging.StreamHandler"}},
    "loggers": {
        "django": {"handlers": ["console"], "level": "WARNING"},
        "django.request": {"handlers": ["console"], "level": "ERROR", "propagate": False},
    },
}
```

- [ ] **Step 9: Create `cartei/settings_test.py`**

```python
"""Test settings: no LDAP, SQLite in-memory, domain models temporarily managed."""
AUTHENTICATION_BACKENDS = ["django.contrib.auth.backends.ModelBackend"]
SECRET_KEY = "test-secret-key-not-for-production"
DEBUG = True
ALLOWED_HOSTS = ["*"]
INSTALLED_APPS = [
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "app",
]
MIDDLEWARE = [
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
]
ROOT_URLCONF = "cartei.urls"
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    }
]
DATABASES = {"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}}
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
LOGIN_URL = "/login/"
LOGIN_REDIRECT_URL = "/abfragen/"
LOGOUT_REDIRECT_URL = "/login/"
STATIC_URL = "static/"
STATIC_ROOT = "/tmp/cartei-test-static"
CARTEI_ADMIN_GROUP = "cn=admins,dc=test"
CARTEI_CLUSTER_GROUP = "cn=cluster,dc=test"
LDAP_GROUPS_BASE = "cn=groups,dc=test"
LDAP_REQUIRE_GROUP = "cn=clearance,dc=test"
LDAP_USER_SEARCH_BASE = "cn=users,dc=test"
```

- [ ] **Step 10: Create `cartei/urls.py`**

```python
from django.contrib.auth import views as auth_views
from django.urls import include, path

urlpatterns = [
    path("login/", auth_views.LoginView.as_view(template_name="app/login.html"), name="login"),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),
    path("", include("app.urls")),
]
```

- [ ] **Step 11: Create `cartei/wsgi.py`**

```python
import os
from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "cartei.settings")
application = get_wsgi_application()
```

- [ ] **Step 12: Create `gunicorn.conf.py`**

```python
import os

bind = "0.0.0.0:8000"
worker_class = "gthread"
workers = int(os.environ.get("GUNICORN_WORKERS", "2"))
threads = int(os.environ.get("GUNICORN_THREADS", "4"))
timeout = int(os.environ.get("GUNICORN_TIMEOUT", "30"))
loglevel = os.environ.get("GUNICORN_LOG_LEVEL", "info")
accesslog = "-"
errorlog = "-"
worker_tmp_dir = "/dev/shm"
```

- [ ] **Step 13: Create `Dockerfile`**

```dockerfile
FROM ghcr.io/astral-sh/uv:python3.14-bookworm-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libldap-dev \
    libsasl2-dev \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml .
RUN uv sync --no-group dev

COPY . .

EXPOSE 8000

CMD ["sh", "-c", \
  "uv run python manage.py migrate --settings=cartei.settings && \
   uv run python manage.py collectstatic --noinput --settings=cartei.settings && \
   uv run gunicorn cartei.wsgi:application --config gunicorn.conf.py"]
```

- [ ] **Step 14: Create `.env.example`**

```
DJANGO_SECRET_KEY=CHANGE_ME
DEBUG=false
ALLOWED_HOSTS=cartei.intranet.ca-hd.de
DATABASE_URL=postgresql+psycopg://cartei:CHANGE_ME@postgres:5432/cartei
HTTPS_ENABLED=true
CSRF_TRUSTED_ORIGINS=https://cartei.intranet.ca-hd.de

LDAP_SERVER_URI=ldaps://ipa.intranet.ca-hd.de
LDAP_BIND_DN=uid=service_cartei,cn=users,cn=accounts,dc=intranet,dc=ca-hd,dc=de
LDAP_BIND_PASSWORD=CHANGE_ME
LDAP_USER_SEARCH_BASE=cn=users,cn=accounts,dc=intranet,dc=ca-hd,dc=de
LDAP_CA_CERT_PATH=/app/certs/ca.pem
LDAP_REQUIRE_GROUP=cn=confidentiality_clearance,cn=groups,cn=accounts,dc=intranet,dc=ca-hd,dc=de
CARTEI_ADMIN_GROUP=cn=ag.it,cn=groups,cn=accounts,dc=intranet,dc=ca-hd,dc=de
CARTEI_CLUSTER_GROUP=cn=gr.cluster,cn=groups,cn=accounts,dc=intranet,dc=ca-hd,dc=de
LDAP_GROUPS_BASE=cn=groups,cn=accounts,dc=intranet,dc=ca-hd,dc=de
```

Note: `DATABASE_URL` uses standard postgres scheme — the `+psycopg` suffix is only needed for SQLAlchemy (cartei_db). Django's psycopg3 backend is selected automatically when `psycopg` is installed. Use `postgresql://...` (no suffix) for the Django `DATABASE_URL`.

- [ ] **Step 15: Create empty `app/__init__.py`, `app/views/__init__.py`, `tests/__init__.py`**

- [ ] **Step 16: Verify Django setup**

```bash
cd /Users/philipp/git-repos/cartei
uv run python manage.py check --settings=cartei.settings_test
```

Expected: `System check identified no issues (0 silenced).`

- [ ] **Step 17: Commit**

```bash
git add .
git commit -m "feat: scaffold cartei Django project"
```

---

## Task 2: Auth Backend and Role Decorator

**Files:**
- Create: `app/auth.py`
- Create: `app/decorators.py`
- Create: `tests/conftest.py`
- Create: `tests/test_auth.py`

**Interfaces:**
- Consumes: `cartei/settings.py` — `CARTEI_ADMIN_GROUP`, `CARTEI_CLUSTER_GROUP`; `app/models.py:Tenant` (Task 3, but conftest makes it available)
- Produces: `CustomLDAPBackend` at `app.auth.CustomLDAPBackend`; `require_group(*groups)` at `app.decorators.require_group`

Note: `app/auth.py` imports `app.models.Tenant`. Since Task 3 comes after this task, write the tests for `_ensure_tenant` as a separate step after Task 3 completes.

- [ ] **Step 1: Create `tests/conftest.py`**

This fixture overrides pytest-django's DB setup to temporarily mark domain models as `managed = True`, so SQLite creates them during tests.

```python
import pytest


@pytest.fixture(scope="session")
def django_db_setup(django_test_environment, django_db_blocker):
    """Make managed=False domain models temporarily managed so SQLite test DB creates them."""
    import django.db.models as djmodels
    from app import models as app_models

    unmanaged = [
        obj
        for name in dir(app_models)
        if isinstance((obj := getattr(app_models, name)), type)
        and issubclass(obj, djmodels.Model)
        and not obj._meta.abstract
        and not obj._meta.managed
    ]
    for m in unmanaged:
        m._meta.managed = True

    with django_db_blocker.unblock():
        from django.test.utils import setup_databases, teardown_databases
        old_config = setup_databases(verbosity=0, interactive=False)

    yield

    with django_db_blocker.unblock():
        teardown_databases(old_config, verbosity=0)

    for m in unmanaged:
        m._meta.managed = False
```

- [ ] **Step 2: Write failing tests for `_dn_to_cn` and `_sync_groups`**

```python
# tests/test_auth.py
import pytest
from unittest.mock import MagicMock, patch
from django.contrib.auth.models import User, Group


def make_ldap_user(member_of):
    """Helper: fake ldap_user with memberOf attribute."""
    ldap_user = MagicMock()
    ldap_user.attrs.get = lambda key, default=None: member_of if key == "memberOf" else (default or [])
    return ldap_user


def test_dn_to_cn_extracts_first_cn():
    from app.auth import _dn_to_cn
    assert _dn_to_cn("cn=ag.kueche,cn=groups,cn=accounts,dc=intranet,dc=ca-hd,dc=de") == "ag.kueche"


def test_dn_to_cn_handles_no_cn():
    from app.auth import _dn_to_cn
    assert _dn_to_cn("something-without-cn") == "something-without-cn"


@pytest.mark.django_db
def test_sync_groups_adds_admins(settings):
    settings.CARTEI_ADMIN_GROUP = "cn=admins,dc=test"
    settings.CARTEI_CLUSTER_GROUP = "cn=cluster,dc=test"

    from app.auth import CustomLDAPBackend
    user = User.objects.create_user(username="alice")
    ldap_user = make_ldap_user(["cn=admins,dc=test", "cn=ag.kueche,dc=test"])
    user.ldap_user = ldap_user

    backend = CustomLDAPBackend()
    backend._sync_groups(user)

    group_names = list(user.groups.values_list("name", flat=True))
    assert "admins" in group_names
    assert "ag.kueche" in group_names
    assert "cluster" not in group_names


@pytest.mark.django_db
def test_sync_groups_adds_cluster(settings):
    settings.CARTEI_ADMIN_GROUP = "cn=admins,dc=test"
    settings.CARTEI_CLUSTER_GROUP = "cn=cluster,dc=test"

    from app.auth import CustomLDAPBackend
    user = User.objects.create_user(username="bob")
    ldap_user = make_ldap_user(["cn=cluster,dc=test"])
    user.ldap_user = ldap_user

    backend = CustomLDAPBackend()
    backend._sync_groups(user)

    assert user.groups.filter(name="cluster").exists()


@pytest.mark.django_db
def test_sync_groups_removes_stale_groups(settings):
    settings.CARTEI_ADMIN_GROUP = "cn=admins,dc=test"
    settings.CARTEI_CLUSTER_GROUP = "cn=cluster,dc=test"

    from app.auth import CustomLDAPBackend
    user = User.objects.create_user(username="carol")
    old_group, _ = Group.objects.get_or_create(name="ag.kueche")
    user.groups.add(old_group)

    # LDAP now shows no groups
    ldap_user = make_ldap_user([])
    user.ldap_user = ldap_user

    backend = CustomLDAPBackend()
    backend._sync_groups(user)

    assert not user.groups.filter(name="ag.kueche").exists()


@pytest.mark.django_db
def test_sync_groups_skips_non_ag_groups(settings):
    settings.CARTEI_ADMIN_GROUP = "cn=admins,dc=test"
    settings.CARTEI_CLUSTER_GROUP = "cn=cluster,dc=test"

    from app.auth import CustomLDAPBackend
    user = User.objects.create_user(username="dave")
    ldap_user = make_ldap_user(["cn=ipausers,dc=test"])  # not ag. prefixed, not admin/cluster
    user.ldap_user = ldap_user

    backend = CustomLDAPBackend()
    backend._sync_groups(user)

    assert user.groups.count() == 0


@pytest.mark.django_db
def test_require_group_denies_wrong_group():
    from django.test import RequestFactory
    from django.core.exceptions import PermissionDenied
    from app.decorators import require_group

    factory = RequestFactory()
    user = User.objects.create_user(username="eve")

    @require_group("admins")
    def protected_view(request):
        return "ok"

    request = factory.get("/")
    request.user = user
    with pytest.raises(PermissionDenied):
        protected_view(request)


@pytest.mark.django_db
def test_require_group_allows_correct_group():
    from django.test import RequestFactory
    from django.http import HttpResponse
    from app.decorators import require_group

    factory = RequestFactory()
    user = User.objects.create_user(username="frank")
    group, _ = Group.objects.get_or_create(name="admins")
    user.groups.add(group)

    @require_group("admins")
    def protected_view(request):
        return HttpResponse("ok")

    request = factory.get("/")
    request.user = user
    response = protected_view(request)
    assert response.status_code == 200
```

- [ ] **Step 3: Run failing tests**

```bash
cd /Users/philipp/git-repos/cartei
uv run pytest tests/test_auth.py -v
```

Expected: ImportError (`cannot import name '_dn_to_cn' from 'app.auth'`)

- [ ] **Step 4: Create `app/auth.py`**

```python
import logging
import uuid as uuid_module

from django.conf import settings
from django.contrib.auth.models import Group
from django_auth_ldap.backend import LDAPBackend

logger = logging.getLogger(__name__)


def _dn_to_cn(dn: str) -> str:
    for part in dn.split(","):
        if part.lower().startswith("cn="):
            return part[3:]
    return dn


class CustomLDAPBackend(LDAPBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        user = super().authenticate(request, username, password, **kwargs)
        if user is not None:
            self._sync_groups(user)
            self._ensure_tenant(user)
        return user

    def _sync_groups(self, user) -> None:
        admin_dn = getattr(settings, "CARTEI_ADMIN_GROUP", "").lower()
        cluster_dn = getattr(settings, "CARTEI_CLUSTER_GROUP", "").lower()
        try:
            member_of: list[str] = user.ldap_user.attrs.get("memberOf", [])
            desired: set[str] = set()
            for dn in member_of:
                dn_l = dn.lower()
                if dn_l == admin_dn:
                    desired.add("admins")
                elif dn_l == cluster_dn:
                    desired.add("cluster")
                else:
                    cn = _dn_to_cn(dn)
                    if cn.startswith("ag."):
                        desired.add(cn)
            current = set(user.groups.values_list("name", flat=True))
            for name in desired - current:
                group, _ = Group.objects.get_or_create(name=name)
                user.groups.add(group)
            for name in current - desired:
                try:
                    user.groups.remove(Group.objects.get(name=name))
                except Group.DoesNotExist:
                    pass
        except Exception as exc:
            logger.error(f"Group sync failed for {user.username!r}: {exc}")

    def _ensure_tenant(self, user) -> None:
        from app.models import Tenant
        if Tenant.objects.filter(intranet_username=user.username).exists():
            return
        try:
            uuid_raw = user.ldap_user.attrs.get("ipaUniqueID", [None])[0]
            if isinstance(uuid_raw, bytes):
                uuid_raw = uuid_raw.decode()
            intranet_uuid = uuid_module.UUID(uuid_raw) if uuid_raw else uuid_module.uuid4()
            Tenant.objects.create(
                first_name=user.first_name or "",
                last_name=user.last_name or "",
                email=user.email or "",
                intranet_username=user.username,
                intranet_uuid=intranet_uuid,
            )
        except Exception as exc:
            logger.error(f"Failed to auto-create Tenant for {user.username!r}: {exc}")
```

- [ ] **Step 5: Create `app/decorators.py`**

```python
from functools import wraps

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied


def require_group(*groups):
    def decorator(view_func):
        @wraps(view_func)
        def _check(request, *args, **kwargs):
            if not request.user.groups.filter(name__in=groups).exists():
                raise PermissionDenied
            return view_func(request, *args, **kwargs)
        return login_required(_check)
    return decorator
```

- [ ] **Step 6: Run tests — verify they pass**

```bash
uv run pytest tests/test_auth.py -v
```

Expected: all tests PASS.

- [ ] **Step 7: Commit**

```bash
git add app/auth.py app/decorators.py tests/conftest.py tests/test_auth.py
git commit -m "feat: add LDAP auth backend and require_group decorator"
```

---

## Task 3: managed=False Django Models

**Files:**
- Create: `app/models.py`
- Create: `tests/test_models.py`

**Interfaces:**
- Consumes: cartei_db schema (Task 0)
- Produces: `Tenant`, `AGAbfrage`, `AGAbfrageResult`, `ClusterNote`, `AGStatus` — importable from `app.models`

- [ ] **Step 1: Write failing tests for model logic**

```python
# tests/test_models.py
from datetime import date, timedelta
import pytest


def abfrage_for_state(state: str):
    """Return (ends_at, grace_ends_at) such that AGAbfrage.state == state."""
    today = date.today()
    if state == "open":
        return today, today + timedelta(days=7)
    if state == "grace":
        return today - timedelta(days=1), today + timedelta(days=6)
    # closed
    return today - timedelta(days=8), today - timedelta(days=1)


@pytest.mark.django_db
def test_abfrage_state_open():
    from app.models import AGAbfrage
    ends_at, grace = abfrage_for_state("open")
    a = AGAbfrage(date=date.today(), ends_at=ends_at, grace_ends_at=grace)
    assert a.state == "open"
    assert a.can_ag_edit() is True


@pytest.mark.django_db
def test_abfrage_state_grace():
    from app.models import AGAbfrage
    ends_at, grace = abfrage_for_state("grace")
    a = AGAbfrage(date=date.today(), ends_at=ends_at, grace_ends_at=grace)
    assert a.state == "grace"
    assert a.can_ag_edit() is True


@pytest.mark.django_db
def test_abfrage_state_closed():
    from app.models import AGAbfrage
    ends_at, grace = abfrage_for_state("closed")
    a = AGAbfrage(date=date.today(), ends_at=ends_at, grace_ends_at=grace)
    assert a.state == "closed"
    assert a.can_ag_edit() is False


@pytest.mark.django_db
def test_tenant_str():
    from app.models import Tenant
    import uuid
    t = Tenant(first_name="Anna", last_name="Muster", intranet_username="amuster",
               intranet_uuid=uuid.uuid4())
    assert "Anna" in str(t)
    assert "Muster" in str(t)


@pytest.mark.django_db
def test_tenant_create_without_move_in(db):
    from app.models import Tenant
    import uuid
    t = Tenant.objects.create(
        first_name="Bob", last_name="Test", email="bob@test.de",
        intranet_username="bobtest", intranet_uuid=uuid.uuid4(),
    )
    assert t.pk is not None
    assert t.move_in is None
```

- [ ] **Step 2: Run failing tests**

```bash
uv run pytest tests/test_models.py -v
```

Expected: ImportError (`cannot import name 'AGAbfrage' from 'app.models'`)

- [ ] **Step 3: Create `app/models.py`**

```python
from decimal import Decimal

from django.db import models


class AGStatus(models.TextChoices):
    ACTIVE = "ACTIVE", "Active"
    NOT_ACTIVE_ENOUGH = "NOT_ACTIVE_ENOUGH", "Not active enough"
    EXEMPT = "EXEMPT", "Exempt"


class Tenant(models.Model):
    first_name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255)
    email = models.CharField(max_length=255, default="")
    intranet_username = models.CharField(max_length=255, unique=True)
    intranet_uuid = models.UUIDField(unique=True)
    preferred_name = models.CharField(max_length=255, null=True, blank=True)
    pronouns = models.CharField(max_length=255, null=True, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    phone = models.CharField(max_length=50, null=True, blank=True)
    is_flinta = models.BooleanField(default=False)
    study_subject = models.CharField(max_length=255, null=True, blank=True)
    apprenticeship_field = models.CharField(max_length=255, null=True, blank=True)
    educational_institution = models.CharField(max_length=255, null=True, blank=True)
    barrier_free_needed = models.BooleanField(default=False)
    mailbox_key = models.BooleanField(default=False)
    mailbox_list_opt_in = models.BooleanField(default=False)
    soli_miete_wunsch = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0"))
    is_sublet = models.BooleanField(default=False)
    sublet_from = models.DateField(null=True, blank=True)
    sublet_to = models.DateField(null=True, blank=True)
    sublet_of_tenant = models.ForeignKey(
        "self", null=True, blank=True, on_delete=models.DO_NOTHING, db_constraint=False
    )
    data_priv_signed_at = models.DateField(null=True, blank=True)
    photo_allowance_signed_at = models.DateField(null=True, blank=True)
    move_in = models.DateField(null=True, blank=True)
    move_out = models.DateField(null=True, blank=True)
    comments = models.TextField(null=True, blank=True)

    class Meta:
        managed = False
        db_table = "tenant"

    def __str__(self) -> str:
        return f"{self.first_name} {self.last_name} ({self.intranet_username})"


class AGAbfrage(models.Model):
    date = models.DateField()
    label = models.CharField(max_length=255, null=True, blank=True)
    ends_at = models.DateField()
    grace_ends_at = models.DateField()

    class Meta:
        managed = False
        db_table = "ag_abfrage"
        ordering = ["-date"]

    def __str__(self) -> str:
        return self.label or str(self.date)

    @property
    def state(self) -> str:
        from datetime import date
        today = date.today()
        if today <= self.ends_at:
            return "open"
        if today <= self.grace_ends_at:
            return "grace"
        return "closed"

    def can_ag_edit(self) -> bool:
        return self.state in ("open", "grace")


class AGAbfrageResult(models.Model):
    abfrage = models.ForeignKey(AGAbfrage, on_delete=models.DO_NOTHING, db_constraint=False)
    ag_name = models.CharField(max_length=255)
    tenant = models.ForeignKey(Tenant, on_delete=models.DO_NOTHING, db_constraint=False)
    status = models.CharField(max_length=50, choices=AGStatus.choices)
    note = models.TextField(null=True, blank=True)

    class Meta:
        managed = False
        db_table = "ag_abfrage_result"


class ClusterNote(models.Model):
    tenant = models.ForeignKey(Tenant, on_delete=models.DO_NOTHING, db_constraint=False)
    abfrage = models.ForeignKey(AGAbfrage, on_delete=models.DO_NOTHING, db_constraint=False)
    note = models.TextField()
    created_at = models.DateTimeField()
    created_by = models.CharField(max_length=255)

    class Meta:
        managed = False
        db_table = "cluster_note"
```

- [ ] **Step 4: Run tests — verify they pass**

```bash
uv run pytest tests/test_models.py -v
```

Expected: all tests PASS.

- [ ] **Step 5: Add `_ensure_tenant` test to `test_auth.py`**

Append to `tests/test_auth.py`:

```python
@pytest.mark.django_db
def test_ensure_tenant_creates_on_first_login():
    from app.auth import CustomLDAPBackend
    from app.models import Tenant

    user = User.objects.create_user(username="greta", first_name="Greta", last_name="X", email="g@ca.de")
    ldap_user = MagicMock()
    ldap_user.attrs.get = lambda key, default=None: [b"some-uuid-string"] if key == "ipaUniqueID" else (default or [])
    user.ldap_user = ldap_user

    backend = CustomLDAPBackend()
    with patch("app.auth.uuid_module.UUID", side_effect=ValueError):
        # UUID parsing fails → falls back to uuid4()
        backend._ensure_tenant(user)

    assert Tenant.objects.filter(intranet_username="greta").exists()


@pytest.mark.django_db
def test_ensure_tenant_skips_if_exists():
    from app.auth import CustomLDAPBackend
    from app.models import Tenant
    import uuid

    Tenant.objects.create(
        first_name="Hanna", last_name="Y", email="h@ca.de",
        intranet_username="hanna", intranet_uuid=uuid.uuid4(),
    )
    user = User.objects.create_user(username="hanna")
    user.ldap_user = MagicMock()

    backend = CustomLDAPBackend()
    backend._ensure_tenant(user)

    # Still only one Tenant record
    assert Tenant.objects.filter(intranet_username="hanna").count() == 1
```

- [ ] **Step 6: Run full test suite**

```bash
uv run pytest -v
```

Expected: all tests PASS.

- [ ] **Step 7: Commit**

```bash
git add app/models.py tests/test_models.py tests/test_auth.py
git commit -m "feat: add managed=False domain models"
```

---

## Task 4: LDAP Utilities and Sync View

**Files:**
- Create: `app/ldap_utils.py`
- Create: `app/views/admin_views.py`
- Create: `app/urls.py`
- Modify: `cartei/urls.py` (add redirect from `/` to `/abfragen/`)
- Create: `tests/test_views_admin.py`

**Interfaces:**
- Consumes: `app/models.py:Tenant`, `app/decorators.py:require_group`, settings: `AUTH_LDAP_SERVER_URI`, `AUTH_LDAP_BIND_DN`, `AUTH_LDAP_BIND_PASSWORD`, `LDAP_USER_SEARCH_BASE`, `LDAP_GROUPS_BASE`, `LDAP_REQUIRE_GROUP`
- Produces: `GET /abfragen/` → abfragen list; `POST /admin/sync-from-ldap/` → JSON `{created, updated}`

- [ ] **Step 1: Write failing tests for the sync view**

```python
# tests/test_views_admin.py
import uuid
import pytest
from unittest.mock import patch
from django.contrib.auth.models import User, Group
from django.test import Client


def _admin_user(username="admin"):
    user = User.objects.create_user(username=username, password="pw")
    group, _ = Group.objects.get_or_create(name="admins")
    user.groups.add(group)
    return user


FAKE_MEMBERS = [
    {"username": "alice", "first_name": "Alice", "last_name": "A", "email": "alice@ca.de", "uuid": str(uuid.uuid4())},
    {"username": "bob",   "first_name": "Bob",   "last_name": "B", "email": "bob@ca.de",   "uuid": str(uuid.uuid4())},
]


@pytest.mark.django_db
def test_sync_requires_admin():
    client = Client()
    user = User.objects.create_user(username="nobody", password="pw")
    client.force_login(user)
    response = client.post("/admin/sync-from-ldap/")
    assert response.status_code == 403


@pytest.mark.django_db
def test_sync_requires_post():
    client = Client()
    user = _admin_user()
    client.force_login(user)
    response = client.get("/admin/sync-from-ldap/")
    assert response.status_code == 405


@pytest.mark.django_db
def test_sync_creates_tenants():
    client = Client()
    client.force_login(_admin_user())

    with patch("app.views.admin_views.ldap_utils.get_clearance_members", return_value=FAKE_MEMBERS):
        response = client.post("/admin/sync-from-ldap/")

    assert response.status_code == 200
    data = response.json()
    assert data["created"] == 2
    assert data["updated"] == 0

    from app.models import Tenant
    assert Tenant.objects.filter(intranet_username="alice").exists()


@pytest.mark.django_db
def test_sync_updates_existing_tenants():
    from app.models import Tenant
    Tenant.objects.create(
        first_name="Old", last_name="Name", email="old@ca.de",
        intranet_username="alice", intranet_uuid=uuid.uuid4(),
    )

    client = Client()
    client.force_login(_admin_user())

    with patch("app.views.admin_views.ldap_utils.get_clearance_members", return_value=FAKE_MEMBERS):
        response = client.post("/admin/sync-from-ldap/")

    data = response.json()
    assert data["created"] == 1  # only bob
    assert data["updated"] == 1  # alice updated

    alice = Tenant.objects.get(intranet_username="alice")
    assert alice.first_name == "Alice"
```

- [ ] **Step 2: Run failing tests**

```bash
uv run pytest tests/test_views_admin.py -v
```

Expected: ImportError or 404 (no urls defined yet).

- [ ] **Step 3: Create `app/ldap_utils.py`**

```python
"""LDAP helper functions for querying group members.

These functions are only called from views that require cluster/admin access.
In tests, patch `app.ldap_utils.get_clearance_members` and `get_ag_members`.
"""
import ldap
from django.conf import settings


def _connect():
    for opt, val in getattr(settings, "AUTH_LDAP_GLOBAL_OPTIONS", {}).items():
        ldap.set_option(opt, val)
    conn = ldap.initialize(settings.AUTH_LDAP_SERVER_URI)
    conn.simple_bind_s(settings.AUTH_LDAP_BIND_DN, settings.AUTH_LDAP_BIND_PASSWORD)
    return conn


def _parse(attrs: dict) -> dict:
    def d(key):
        v = attrs.get(key, [b""])[0]
        return v.decode() if isinstance(v, bytes) else (v or "")

    return {
        "username": d("uid"),
        "first_name": d("givenName"),
        "last_name": d("sn"),
        "email": d("mail"),
        "uuid": d("ipaUniqueID"),
    }


_ATTRS = ["uid", "givenName", "sn", "mail", "ipaUniqueID"]


def get_clearance_members() -> list[dict]:
    """Return all members of LDAP_REQUIRE_GROUP (confidentiality_clearance)."""
    conn = _connect()
    results = conn.search_s(
        settings.LDAP_USER_SEARCH_BASE,
        ldap.SCOPE_SUBTREE,
        f"(memberOf={settings.LDAP_REQUIRE_GROUP})",
        _ATTRS,
    )
    return [_parse(attrs) for _, attrs in results if attrs]


def get_ag_members(ag_name: str) -> list[dict]:
    """Return members of LDAP group cn=<ag_name>,<LDAP_GROUPS_BASE>."""
    group_dn = f"cn={ag_name},{settings.LDAP_GROUPS_BASE}"
    conn = _connect()
    results = conn.search_s(
        settings.LDAP_USER_SEARCH_BASE,
        ldap.SCOPE_SUBTREE,
        f"(memberOf={group_dn})",
        _ATTRS,
    )
    return [_parse(attrs) for _, attrs in results if attrs]
```

- [ ] **Step 4: Create `app/views/admin_views.py`**

```python
import uuid as uuid_module

from django.http import JsonResponse
from django.views.decorators.http import require_POST

from app import ldap_utils
from app.decorators import require_group
from app.models import Tenant


@require_POST
@require_group("admins")
def sync_from_ldap(request):
    """Bulk-sync all confidentiality_clearance LDAP members to Tenant records."""
    members = ldap_utils.get_clearance_members()
    created = updated = 0
    for m in members:
        try:
            intranet_uuid = uuid_module.UUID(m["uuid"]) if m["uuid"] else uuid_module.uuid4()
        except ValueError:
            intranet_uuid = uuid_module.uuid4()

        tenant, was_created = Tenant.objects.get_or_create(
            intranet_username=m["username"],
            defaults={
                "intranet_uuid": intranet_uuid,
                "first_name": m["first_name"],
                "last_name": m["last_name"],
                "email": m["email"],
            },
        )
        if was_created:
            created += 1
        else:
            Tenant.objects.filter(pk=tenant.pk).update(
                first_name=m["first_name"],
                last_name=m["last_name"],
                email=m["email"],
                intranet_uuid=intranet_uuid,
            )
            updated += 1

    return JsonResponse({"created": created, "updated": updated})
```

- [ ] **Step 5: Create `app/urls.py`**

```python
from django.urls import path

from app.views import admin_views

urlpatterns = [
    path("admin/sync-from-ldap/", admin_views.sync_from_ldap, name="sync_from_ldap"),
]
```

- [ ] **Step 6: Update `cartei/urls.py` to add redirect and include app urls**

```python
from django.contrib.auth import views as auth_views
from django.shortcuts import redirect
from django.urls import include, path


def _root(request):
    return redirect("abfragen_list")


urlpatterns = [
    path("", _root),
    path("login/", auth_views.LoginView.as_view(template_name="app/login.html"), name="login"),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),
    path("", include("app.urls")),
]
```

- [ ] **Step 7: Run tests — verify they pass**

```bash
uv run pytest tests/test_views_admin.py -v
```

Expected: all tests PASS.

- [ ] **Step 8: Commit**

```bash
git add app/ldap_utils.py app/views/admin_views.py app/urls.py cartei/urls.py tests/test_views_admin.py
git commit -m "feat: add LDAP sync view and app URL routing"
```

---

## Task 5: AG Engagement Views and Templates

**Files:**
- Create: `app/views/abfragen.py`
- Update: `app/urls.py`
- Create: `app/templates/app/base.html`
- Create: `app/templates/app/login.html`
- Create: `app/templates/app/abfragen/list.html`
- Create: `app/templates/app/abfragen/new.html`
- Create: `app/templates/app/abfragen/detail.html`
- Create: `app/templates/app/abfragen/ag_edit.html`
- Create: `app/templates/app/abfragen/tenants.html`
- Create: `tests/test_views_abfragen.py`

**Interfaces:**
- Consumes: `app/models.py`, `app/ldap_utils.py`, `app/decorators.py`, `app/urls.py` (admin route from Task 4)
- Produces: All AG engagement URL patterns; HTML views

- [ ] **Step 1: Write failing tests for the engagement views**

```python
# tests/test_views_abfragen.py
import uuid
from datetime import date, timedelta
import pytest
from unittest.mock import patch
from django.contrib.auth.models import User, Group
from django.test import Client


def _open_abfrage():
    from app.models import AGAbfrage
    today = date.today()
    return AGAbfrage.objects.create(
        date=today,
        label="Test Abfrage",
        ends_at=today + timedelta(days=7),
        grace_ends_at=today + timedelta(days=14),
    )


def _closed_abfrage():
    from app.models import AGAbfrage
    today = date.today()
    return AGAbfrage.objects.create(
        date=today - timedelta(days=30),
        ends_at=today - timedelta(days=15),
        grace_ends_at=today - timedelta(days=8),
    )


def _user_in_group(username, *group_names):
    user = User.objects.create_user(username=username, password="pw")
    for name in group_names:
        g, _ = Group.objects.get_or_create(name=name)
        user.groups.add(g)
    return user


@pytest.mark.django_db
def test_list_requires_login():
    client = Client()
    response = client.get("/abfragen/")
    assert response.status_code == 302
    assert "/login/" in response["Location"]


@pytest.mark.django_db
def test_list_shows_abfragen():
    _open_abfrage()
    client = Client()
    client.force_login(User.objects.create_user(username="viewer"))
    response = client.get("/abfragen/")
    assert response.status_code == 200
    assert b"Test Abfrage" in response.content


@pytest.mark.django_db
def test_new_abfrage_requires_privileged():
    client = Client()
    client.force_login(User.objects.create_user(username="nobody"))
    response = client.post("/abfragen/new/", {
        "date": "2024-09-01",
        "label": "Test",
        "ends_at": "2024-09-30",
        "grace_ends_at": "2024-10-07",
    })
    assert response.status_code == 403


@pytest.mark.django_db
def test_new_abfrage_creates_and_redirects():
    client = Client()
    client.force_login(_user_in_group("clusteruser", "cluster"))
    response = client.post("/abfragen/new/", {
        "date": "2024-09-01",
        "label": "Q3 2024",
        "ends_at": "2024-09-30",
        "grace_ends_at": "2024-10-07",
    })
    assert response.status_code == 302
    from app.models import AGAbfrage
    assert AGAbfrage.objects.filter(label="Q3 2024").exists()


@pytest.mark.django_db
def test_ag_edit_denies_wrong_ag():
    abfrage = _open_abfrage()
    user = _user_in_group("kueche_user", "ag.kueche")
    client = Client()
    client.force_login(user)
    # User is in ag.kueche but tries to edit ag.garten
    response = client.get(f"/abfragen/{abfrage.pk}/ag/ag.garten/")
    assert response.status_code == 403


@pytest.mark.django_db
def test_ag_edit_allows_own_ag():
    abfrage = _open_abfrage()
    user = _user_in_group("kueche_user2", "ag.kueche")
    client = Client()
    client.force_login(user)

    fake_members = [{"username": "kueche_user2", "first_name": "K", "last_name": "U", "email": "k@ca.de", "uuid": str(uuid.uuid4())}]
    with patch("app.views.abfragen.ldap_utils.get_ag_members", return_value=fake_members):
        response = client.get(f"/abfragen/{abfrage.pk}/ag/ag.kueche/")
    assert response.status_code == 200


@pytest.mark.django_db
def test_ag_edit_closed_returns_closed_page():
    abfrage = _closed_abfrage()
    user = _user_in_group("kueche_user3", "ag.kueche")
    client = Client()
    client.force_login(user)

    with patch("app.views.abfragen.ldap_utils.get_ag_members", return_value=[]):
        response = client.get(f"/abfragen/{abfrage.pk}/ag/ag.kueche/")
    assert response.status_code == 200
    assert b"geschlossen" in response.content


@pytest.mark.django_db
def test_ag_edit_post_saves_result():
    from app.models import AGAbfrage, AGAbfrageResult, Tenant
    abfrage = _open_abfrage()
    tenant = Tenant.objects.create(
        first_name="T", last_name="U", email="tu@ca.de",
        intranet_username="tu_post", intranet_uuid=uuid.uuid4(),
    )
    user = _user_in_group("tu_post", "ag.kueche")
    client = Client()
    client.force_login(user)

    fake_members = [{"username": "tu_post", "first_name": "T", "last_name": "U", "email": "tu@ca.de", "uuid": str(tenant.intranet_uuid)}]
    with patch("app.views.abfragen.ldap_utils.get_ag_members", return_value=fake_members):
        response = client.post(
            f"/abfragen/{abfrage.pk}/ag/ag.kueche/",
            {f"status_{tenant.pk}": "ACTIVE", f"note_{tenant.pk}": "Good work"},
        )

    assert response.status_code == 302
    result = AGAbfrageResult.objects.get(abfrage=abfrage, tenant=tenant, ag_name="ag.kueche")
    assert result.status == "ACTIVE"
    assert result.note == "Good work"


@pytest.mark.django_db
def test_tenants_view_requires_privileged():
    abfrage = _open_abfrage()
    user = User.objects.create_user(username="nobody2")
    client = Client()
    client.force_login(user)
    response = client.get(f"/abfragen/{abfrage.pk}/tenants/")
    assert response.status_code == 403
```

- [ ] **Step 2: Run failing tests**

```bash
uv run pytest tests/test_views_abfragen.py -v
```

Expected: ImportError (no views or URLs defined).

- [ ] **Step 3: Create `app/views/abfragen.py`**

```python
from datetime import datetime, timezone

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.http import HttpRequest
from django.shortcuts import get_object_or_404, redirect, render

from app import ldap_utils
from app.decorators import require_group
from app.models import AGAbfrage, AGAbfrageResult, ClusterNote, Tenant

_STATUS_CHOICES = [
    ("ACTIVE", "Aktiv"),
    ("NOT_ACTIVE_ENOUGH", "Nicht aktiv genug"),
    ("EXEMPT", "Befreit"),
]


@login_required
def abfragen_list(request: HttpRequest):
    abfragen = AGAbfrage.objects.all()
    is_privileged = request.user.groups.filter(name__in=["admins", "cluster"]).exists()
    return render(request, "app/abfragen/list.html", {
        "abfragen": abfragen,
        "is_privileged": is_privileged,
    })


@require_group("admins", "cluster")
def abfrage_new(request: HttpRequest):
    if request.method == "POST":
        abfrage = AGAbfrage.objects.create(
            date=request.POST["date"],
            label=request.POST.get("label") or None,
            ends_at=request.POST["ends_at"],
            grace_ends_at=request.POST["grace_ends_at"],
        )
        return redirect("abfrage_detail", pk=abfrage.pk)
    return render(request, "app/abfragen/new.html")


@require_group("admins", "cluster")
def abfrage_detail(request: HttpRequest, pk: int):
    abfrage = get_object_or_404(AGAbfrage, pk=pk)
    results = AGAbfrageResult.objects.filter(abfrage=abfrage).select_related("tenant")
    by_ag: dict[str, list] = {}
    for r in results:
        by_ag.setdefault(r.ag_name, []).append(r)
    return render(request, "app/abfragen/detail.html", {
        "abfrage": abfrage,
        "by_ag": by_ag,
    })


@login_required
def ag_edit(request: HttpRequest, pk: int, ag_name: str):
    abfrage = get_object_or_404(AGAbfrage, pk=pk)
    user_groups = set(request.user.groups.values_list("name", flat=True))
    is_privileged = bool(user_groups & {"admins", "cluster"})

    if not is_privileged and ag_name not in user_groups:
        raise PermissionDenied

    if not is_privileged and not abfrage.can_ag_edit():
        return render(request, "app/abfragen/ag_edit.html", {
            "abfrage": abfrage,
            "ag_name": ag_name,
            "closed": True,
            "rows": [],
        })

    members = ldap_utils.get_ag_members(ag_name)
    usernames = [m["username"] for m in members]
    tenants_by_username = {
        t.intranet_username: t
        for t in Tenant.objects.filter(intranet_username__in=usernames)
    }

    if request.method == "POST":
        for username, tenant in tenants_by_username.items():
            key = f"status_{tenant.pk}"
            if key in request.POST:
                # ponytail: last-write-wins; unique constraint on (abfrage,ag,tenant) would prevent races
                AGAbfrageResult.objects.update_or_create(
                    abfrage=abfrage,
                    ag_name=ag_name,
                    tenant=tenant,
                    defaults={
                        "status": request.POST[key],
                        "note": request.POST.get(f"note_{tenant.pk}", "").strip() or None,
                    },
                )
        return redirect("ag_edit", pk=pk, ag_name=ag_name)

    existing = {
        r.tenant_id: r
        for r in AGAbfrageResult.objects.filter(abfrage=abfrage, ag_name=ag_name)
    }
    rows = [
        {
            "member": m,
            "tenant": (t := tenants_by_username.get(m["username"])),
            "result": existing.get(t.pk) if t else None,
        }
        for m in members
    ]
    return render(request, "app/abfragen/ag_edit.html", {
        "abfrage": abfrage,
        "ag_name": ag_name,
        "rows": rows,
        "status_choices": _STATUS_CHOICES,
        "closed": False,
    })


@require_group("admins", "cluster")
def abfrage_tenants(request: HttpRequest, pk: int):
    abfrage = get_object_or_404(AGAbfrage, pk=pk)
    tenants = Tenant.objects.filter(move_out__isnull=True)

    results_by_tenant: dict[int, list] = {}
    for r in AGAbfrageResult.objects.filter(abfrage=abfrage):
        results_by_tenant.setdefault(r.tenant_id, []).append(r)

    notes = {n.tenant_id: n for n in ClusterNote.objects.filter(abfrage=abfrage)}

    if request.method == "POST":
        tenant_id = request.POST.get("note_tenant_id")
        note_text = request.POST.get("note_text", "").strip()
        if tenant_id and note_text:
            ClusterNote.objects.update_or_create(
                tenant_id=tenant_id,
                abfrage=abfrage,
                defaults={
                    "note": note_text,
                    "created_at": datetime.now(tz=timezone.utc),
                    "created_by": request.user.username,
                },
            )
        return redirect("abfrage_tenants", pk=pk)

    rows = [
        {
            "tenant": t,
            "results": results_by_tenant.get(t.pk, []),
            "sufficient": any(r.status == "ACTIVE" for r in results_by_tenant.get(t.pk, [])),
            "note": notes.get(t.pk),
        }
        for t in tenants
    ]
    return render(request, "app/abfragen/tenants.html", {
        "abfrage": abfrage,
        "rows": rows,
    })
```

- [ ] **Step 4: Update `app/urls.py` with all engagement routes**

```python
from django.urls import path

from app.views import abfragen, admin_views

urlpatterns = [
    path("abfragen/", abfragen.abfragen_list, name="abfragen_list"),
    path("abfragen/new/", abfragen.abfrage_new, name="abfrage_new"),
    path("abfragen/<int:pk>/", abfragen.abfrage_detail, name="abfrage_detail"),
    path("abfragen/<int:pk>/ag/<str:ag_name>/", abfragen.ag_edit, name="ag_edit"),
    path("abfragen/<int:pk>/tenants/", abfragen.abfrage_tenants, name="abfrage_tenants"),
    path("admin/sync-from-ldap/", admin_views.sync_from_ldap, name="sync_from_ldap"),
]
```

- [ ] **Step 5: Create templates**

Create directory structure:
```bash
mkdir -p app/templates/app/abfragen
```

**`app/templates/app/base.html`:**
```html
<!DOCTYPE html>
<html lang="de">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>{% block title %}CArtei{% endblock %}</title>
    <style>
        body { font-family: sans-serif; max-width: 960px; margin: 0 auto; padding: 1rem; }
        nav { margin-bottom: 1rem; padding-bottom: 0.5rem; border-bottom: 1px solid #ccc; }
        nav a { margin-right: 0.5rem; }
        table { border-collapse: collapse; width: 100%; margin: 1rem 0; }
        th, td { border: 1px solid #ddd; padding: 0.4rem 0.6rem; text-align: left; }
        th { background: #f5f5f5; }
        .badge { padding: 2px 6px; border-radius: 3px; font-size: 0.85em; font-weight: bold; }
        .badge-open   { background: #d4edda; color: #155724; }
        .badge-grace  { background: #fff3cd; color: #856404; }
        .badge-closed { background: #f8d7da; color: #721c24; }
        .messages { list-style: none; padding: 0; }
        .messages li { padding: 0.5rem; margin: 0.5rem 0; border-radius: 3px; background: #e2e3e5; }
        button, input[type=submit] { cursor: pointer; padding: 0.3rem 0.8rem; }
        label { display: block; margin: 0.5rem 0; }
        input, select, textarea { padding: 0.3rem; }
    </style>
</head>
<body>
<nav>
    <strong>CArtei</strong>
    | <a href="{% url 'abfragen_list' %}">Abfragen</a>
    {% if request.user.is_authenticated %}
    | {{ request.user.get_full_name|default:request.user.username }}
    | <a href="{% url 'logout' %}">Abmelden</a>
    {% endif %}
</nav>
<main>
{% if messages %}
<ul class="messages">
{% for message in messages %}<li>{{ message }}</li>{% endfor %}
</ul>
{% endif %}
{% block content %}{% endblock %}
</main>
</body>
</html>
```

**`app/templates/app/login.html`:**
```html
{% extends "app/base.html" %}
{% block title %}Anmelden — CArtei{% endblock %}
{% block content %}
<h1>Anmelden</h1>
<form method="post">
    {% csrf_token %}
    {{ form.as_p }}
    <button type="submit">Anmelden</button>
</form>
{% endblock %}
```

**`app/templates/app/abfragen/list.html`:**
```html
{% extends "app/base.html" %}
{% block title %}Abfragen — CArtei{% endblock %}
{% block content %}
<h1>AG-Engagement-Abfragen</h1>
{% if is_privileged %}
<p><a href="{% url 'abfrage_new' %}">+ Neue Abfrage erstellen</a></p>
{% endif %}
<table>
    <thead>
        <tr><th>Datum</th><th>Bezeichnung</th><th>Status</th><th>Endet am</th><th>Nachfrist bis</th><th></th></tr>
    </thead>
    <tbody>
    {% for abfrage in abfragen %}
    <tr>
        <td>{{ abfrage.date }}</td>
        <td>{{ abfrage.label|default:"—" }}</td>
        <td><span class="badge badge-{{ abfrage.state }}">{{ abfrage.state }}</span></td>
        <td>{{ abfrage.ends_at }}</td>
        <td>{{ abfrage.grace_ends_at }}</td>
        <td><a href="{% url 'abfrage_detail' abfrage.pk %}">Details</a></td>
    </tr>
    {% empty %}
    <tr><td colspan="6">Keine Abfragen vorhanden.</td></tr>
    {% endfor %}
    </tbody>
</table>
{% endblock %}
```

**`app/templates/app/abfragen/new.html`:**
```html
{% extends "app/base.html" %}
{% block title %}Neue Abfrage — CArtei{% endblock %}
{% block content %}
<h1>Neue Abfrage erstellen</h1>
<form method="post">
    {% csrf_token %}
    <label>Datum: <input type="date" name="date" required></label>
    <label>Bezeichnung (optional): <input type="text" name="label"></label>
    <label>Offizielle Deadline (endet am): <input type="date" name="ends_at" required></label>
    <label>Nachfrist bis: <input type="date" name="grace_ends_at" required></label>
    <br>
    <button type="submit">Erstellen</button>
    <a href="{% url 'abfragen_list' %}">Abbrechen</a>
</form>
{% endblock %}
```

**`app/templates/app/abfragen/detail.html`:**
```html
{% extends "app/base.html" %}
{% block title %}{{ abfrage }} — CArtei{% endblock %}
{% block content %}
<h1>{{ abfrage }}</h1>
<p>
    Status: <span class="badge badge-{{ abfrage.state }}">{{ abfrage.state }}</span>
    | Endet: {{ abfrage.ends_at }}
    | Nachfrist: {{ abfrage.grace_ends_at }}
</p>
<p><a href="{% url 'abfrage_tenants' abfrage.pk %}">Alle Bewohner:innen anzeigen</a></p>

<h2>Ergebnisse nach AG</h2>
{% if by_ag %}
<table>
    <thead><tr><th>AG</th><th>Bewohner:in</th><th>Status</th><th>Notiz</th></tr></thead>
    <tbody>
    {% for ag_name, results in by_ag.items %}
    {% for r in results %}
    <tr>
        {% if forloop.first %}
        <td rowspan="{{ results|length }}"><a href="{% url 'ag_edit' abfrage.pk ag_name %}">{{ ag_name }}</a></td>
        {% endif %}
        <td>{{ r.tenant }}</td>
        <td>{{ r.status }}</td>
        <td>{{ r.note|default:"—" }}</td>
    </tr>
    {% endfor %}
    {% endfor %}
    </tbody>
</table>
{% else %}
<p>Noch keine Ergebnisse.</p>
{% endif %}
{% endblock %}
```

**`app/templates/app/abfragen/ag_edit.html`:**
```html
{% extends "app/base.html" %}
{% block title %}{{ ag_name }} — {{ abfrage }} — CArtei{% endblock %}
{% block content %}
<h1>{{ ag_name }} — {{ abfrage }}</h1>
<p>
    Status: <span class="badge badge-{{ abfrage.state }}">{{ abfrage.state }}</span>
    | Deadline: {{ abfrage.ends_at }}
    | Nachfrist: {{ abfrage.grace_ends_at }}
</p>
<p><a href="{% url 'abfrage_detail' abfrage.pk %}">← Zur Übersicht</a></p>

{% if closed %}
<p><strong>Diese Abfrage ist geschlossen.</strong> Bearbeitungen sind nicht mehr möglich.</p>
{% else %}
<form method="post">
    {% csrf_token %}
    <table>
        <thead>
            <tr><th>Bewohner:in</th><th>Status</th><th>Notiz (optional)</th></tr>
        </thead>
        <tbody>
        {% for row in rows %}
        <tr>
            <td>{{ row.member.first_name }} {{ row.member.last_name }}
                {% if not row.tenant %}<br><em style="color:#999">(kein Eintrag im System)</em>{% endif %}
            </td>
            {% if row.tenant %}
            <td>
                <select name="status_{{ row.tenant.pk }}" required>
                {% for val, label in status_choices %}
                <option value="{{ val }}"{% if row.result and row.result.status == val %} selected{% endif %}>{{ label }}</option>
                {% endfor %}
                </select>
            </td>
            <td>
                <textarea name="note_{{ row.tenant.pk }}" rows="2" cols="40">{{ row.result.note|default:"" }}</textarea>
            </td>
            {% else %}
            <td colspan="2"><em>Nicht im System — bitte LDAP-Sync durchführen</em></td>
            {% endif %}
        </tr>
        {% empty %}
        <tr><td colspan="3">Keine AG-Mitglieder in LDAP gefunden.</td></tr>
        {% endfor %}
        </tbody>
    </table>
    <br>
    <button type="submit">Speichern</button>
</form>
{% endif %}
{% endblock %}
```

**`app/templates/app/abfragen/tenants.html`:**
```html
{% extends "app/base.html" %}
{% block title %}Bewohner:innen — {{ abfrage }} — CArtei{% endblock %}
{% block content %}
<h1>Bewohner:innen — {{ abfrage }}</h1>
<p><a href="{% url 'abfrage_detail' abfrage.pk %}">← Zur Übersicht</a></p>

<table>
    <thead>
        <tr>
            <th>Name</th>
            <th>Username</th>
            <th>Ergebnis(se)</th>
            <th>Ausreichend?</th>
            <th>Cluster-Notiz</th>
            <th>Notiz bearbeiten</th>
        </tr>
    </thead>
    <tbody>
    {% for row in rows %}
    <tr>
        <td>{{ row.tenant }}</td>
        <td>{{ row.tenant.intranet_username }}</td>
        <td>
            {% for r in row.results %}
            {{ r.ag_name }}: {{ r.status }}{% if not forloop.last %}<br>{% endif %}
            {% empty %}—{% endfor %}
        </td>
        <td>{% if row.sufficient %}✓ Ja{% else %}✗ Nein{% endif %}</td>
        <td>{{ row.note.note|default:"—" }}</td>
        <td>
            <form method="post" style="display:flex;gap:0.3rem">
                {% csrf_token %}
                <input type="hidden" name="note_tenant_id" value="{{ row.tenant.pk }}">
                <input type="text" name="note_text" value="{{ row.note.note|default:'' }}" placeholder="Interne Notiz">
                <button type="submit">OK</button>
            </form>
        </td>
    </tr>
    {% empty %}
    <tr><td colspan="6">Keine aktiven Bewohner:innen.</td></tr>
    {% endfor %}
    </tbody>
</table>
{% endblock %}
```

- [ ] **Step 6: Run failing tests**

```bash
uv run pytest tests/test_views_abfragen.py -v
```

Expected: FAIL because templates don't exist yet (TemplateDoesNotExist). Once templates are created in step 5 above, re-run.

- [ ] **Step 7: Run all tests — verify everything passes**

```bash
uv run pytest -v
```

Expected: all tests PASS. Fix any regressions.

- [ ] **Step 8: Verify Django check passes**

```bash
uv run python manage.py check --settings=cartei.settings_test
```

- [ ] **Step 9: Commit**

```bash
git add app/views/abfragen.py app/urls.py app/templates/ tests/test_views_abfragen.py
git commit -m "feat: add AG engagement views and templates"
```

- [ ] **Step 10: Push to GitHub**

```bash
git push -u origin main
```

---

## Post-Implementation Checklist

After all tasks complete, verify the full integration:

**In `cartei_db`:**
- [ ] `uv run alembic upgrade head` succeeds against a clean DB
- [ ] `uv run pytest` passes

**In `cartei`:**
- [ ] `uv run pytest` passes
- [ ] `uv run python manage.py check` passes (with a real `DATABASE_URL` set to the migrated DB)
- [ ] `uv run python manage.py migrate` creates Django's session/auth tables
- [ ] Application starts: `DATABASE_URL=... uv run gunicorn cartei.wsgi:application --config gunicorn.conf.py`

**In `cartei_deployment`:**
The deployment repo already has placeholder `app` container referencing `ghcr.io/collegiumacademicum/cartei:latest`. No changes needed until CI/CD builds the image.

---

## Notes for Implementer

- `managed = False` means Django never runs `CREATE TABLE` for domain models. Alembic owns those tables. Django's `migrate` only creates `auth_*`, `django_session`, `django_content_type`.
- In tests, the conftest temporarily flips `managed = True` so SQLite creates all tables — this is why tests use SQLite and not PostgreSQL.
- `ldap_utils.py` functions require `python-ldap` to be installed and LDAP reachable. In all tests that touch views calling these functions, patch them with `unittest.mock.patch`.
- `AUTH_LDAP_REQUIRE_GROUP` in `settings.py` is respected by `django-auth-ldap` itself — no custom code needed to enforce the login restriction.
- The `require_group` decorator issues a 403 (PermissionDenied), not a redirect. Only anonymous users get redirected to login (via `login_required` inside the decorator).
- `AGAbfrageResult.update_or_create` in `ag_edit` is last-write-wins. For CA's scale (< 200 concurrent users), this is safe. Add a DB-level unique constraint on `(abfrage_id, ag_name, tenant_id)` in a future cartei_db migration if concurrent editing becomes a concern.
