# CArtei App — Design Spec

**Date:** 2026-08-05
**Project:** cartei (Django web application)
**Repo:** `github.com/CollegiumAcademicum/cartei` (to be created)
**Depends on:** `cartei_db` (schema source of truth)

---

## 1. Purpose

A Django web application that serves as the primary management interface for the Collegium Academicum (CA) tenant management system. The initial MVP focuses on the AG engagement check workflow and bootstrapping tenant records from LDAP. A browser-based UI is a central deliverable, not an afterthought.

---

## 2. Architecture

### Overview

One Django app (`app/`) inside one Django project (`cartei/`). No microservices. Django handles auth, sessions, views, and templates. The database schema is owned by `cartei_db` (Alembic migrations); Django uses `managed = False` models that mirror those tables. Django's own `migrate` only creates its internal tables (sessions, auth, admin).

### Tech stack

- **Python 3.14**
- **Django ≥ 5.x**
- **django-auth-ldap + python-ldap** — LDAP authentication (same stack as mattermost webui)
- **gunicorn** — WSGI server
- **PostgreSQL** via `psycopg` — shared database with `cartei_db` schema
- **Jinja2 / Django templates** — server-rendered UI

### Deployment

The app is deployed as `ghcr.io/collegiumacademicum/cartei:latest` and referenced in `cartei_deployment/docker-compose.yaml`. The `migrate` one-shot container (from `cartei_db` image) runs Alembic migrations before the app starts. Django's `manage.py migrate` only runs for Django's own tables (sessions, auth).

---

## 3. Authentication

Copied and adapted from `mattermost_bots/webui/broadcast/auth.py` and `webui/settings.py`.

- **Backend:** `CustomLDAPBackend(LDAPBackend)` — binds with user credentials, then syncs Django groups from LDAP `memberOf` attributes on every successful login.
- **Login restriction:** `AUTH_LDAP_REQUIRE_GROUP` set to the `confidentiality_clearance` group DN — django-auth-ldap rejects anyone not in that group before a session is created. No custom code needed.
- **Session-based auth** — standard Django sessions, cookie-based. Works seamlessly for the browser UI.
- **FreeIPA specifics:** `OPT_REFERRALS=0`, TLS with CA cert via `LDAP_CA_CERT_PATH`.
- **Service account:** `LDAP_BIND_DN` / `LDAP_BIND_PASSWORD` env vars for group lookups.

### Environment variables

```
LDAP_SERVER_URI=ldaps://ipa.intranet.ca-hd.de
LDAP_BIND_DN=uid=service_cartei,cn=users,cn=accounts,dc=intranet,dc=ca-hd,dc=de
LDAP_BIND_PASSWORD=CHANGE_ME
LDAP_USER_SEARCH_BASE=cn=users,cn=accounts,dc=intranet,dc=ca-hd,dc=de
LDAP_CA_CERT_PATH=/app/certs/ca.pem
CARTEI_ADMIN_GROUP=cn=ag.it,cn=groups,cn=accounts,dc=intranet,dc=ca-hd,dc=de
CARTEI_CLUSTER_GROUP=cn=gr.cluster,cn=groups,cn=accounts,dc=intranet,dc=ca-hd,dc=de
LDAP_REQUIRE_GROUP=cn=confidentiality_clearance,cn=groups,cn=accounts,dc=intranet,dc=ca-hd,dc=de
```

---

## 4. Role System

LDAP group memberships are synced to Django groups on every login by `CustomLDAPBackend._sync_groups()`.

| LDAP group | Django group | Capability |
|---|---|---|
| `$CARTEI_ADMIN_GROUP` (default: `ag.it`) | `admins` | Full access to everything |
| `$CARTEI_CLUSTER_GROUP` (`gr.cluster`) | `cluster` | All AG results, internal notes, unrestricted edit of evaluations |
| `ag.kueche`, `ag.garten`, … (CN parsed from full DN) | `ag.kueche`, … | Enter/edit evaluations for their own AG during open period or grace period |
| Any authenticated CA resident | — | Own profile read/edit, enrollment proof upload |

**Note:** `CARTEI_ADMIN_GROUP` defaults to `ag.it` for the initial launch. When CA creates a dedicated admin LDAP group, update the env var — no code change needed.

Access control in views uses a `require_group(*groups)` decorator (wraps `@login_required` + group membership check). Field-level visibility (e.g. hiding `is_flinta`, `deposit_iban` from non-admins) is handled in view context, not in model layer.

---

## 5. Data Access

Django models in `app/models.py` mirror the `cartei_db` schema with `managed = False`. Alembic (one-shot container from `cartei_db` image) is the sole schema migration tool. Django never alters domain tables.

```python
class Tenant(models.Model):
    class Meta:
        managed = False
        db_table = "tenant"
    # ... fields matching cartei_db schema
```

Django's own tables (sessions, auth groups, admin log) are managed by Django migrations normally.

---

## 6. AG Engagement Check Workflow (MVP)

### Data model changes required in `cartei_db` before app development

- `AGAbfrage`: add `ends_at: date`, `grace_ends_at: date`
- `AGAbfrageResult`: add `note: Optional[str]`
- New table: `ClusterNote(id, tenant_id, abfrage_id, note, created_at, created_by)` — internal Cluster notes per tenant per round, never visible to AG members

### Period logic

An `AGAbfrage` has three states derived from today's date vs its fields:

| State | Condition | Who can edit results |
|---|---|---|
| Open | `today <= ends_at` | AG members (own AG), `cluster`, `admins` |
| Grace | `ends_at < today <= grace_ends_at` | AG members (own AG), `cluster`, `admins` |
| Closed | `today > grace_ends_at` | `cluster`, `admins` only |

### Workflow

1. `admins` or `cluster` creates an `AGAbfrage` (date, label, `ends_at`, `grace_ends_at`)
2. AG members log in and see the current open Abfrage
3. For each member of their AG (fetched from LDAP group members by CN, e.g. `ag.kueche`): set `AGStatus` + optional note. `AGAbfrageResult.ag_name` stores the short CN (e.g. `ag.kueche`), not the full DN.
4. Last save wins — no explicit "submit" step; the Abfrage closing date is the deadline
5. `cluster` reviews results: per-AG view and per-tenant view
6. `cluster` can add `ClusterNote` per tenant per round (internal, not shown to AGs)
7. Derived engagement status per tenant: `ACTIVE` in at least one AG = sufficient engagement

### Key views

| URL | Who | What |
|---|---|---|
| `GET /abfragen/` | all authenticated | List of Abfragen (current + history) |
| `POST /abfragen/new/` | admins, cluster | Create new Abfrage |
| `GET /abfragen/<id>/` | admins, cluster | Overview: all AGs, all results |
| `GET /abfragen/<id>/ag/<ag_name>/` | AG members (own AG), admins, cluster | Edit form for this AG's results |
| `POST /abfragen/<id>/ag/<ag_name>/` | AG members (own AG), admins, cluster | Save results |
| `GET /abfragen/<id>/tenants/` | admins, cluster | Per-tenant view with history and engagement status |

---

## 7. LDAP Tenant Sync

`LDAP_REQUIRE_GROUP` (`confidentiality_clearance`) defines exactly who has access to CArtei — and therefore who should have a `Tenant` record. No separate residents group needed.

Two mechanisms:

**Auto-create on first login:** `CustomLDAPBackend.authenticate()` creates a minimal `Tenant` record (LDAP-sourced fields only) if none exists for the logging-in user. Zero admin action needed for individuals.

**Bulk sync endpoint** `POST /admin/sync-from-ldap/` — admin-only, queries all members of `LDAP_REQUIRE_GROUP` and creates/updates Tenant records in bulk. Useful for bootstrapping before anyone has logged in. Returns a summary: N created, M updated.

LDAP-sourced fields (always synced): `first_name`, `last_name`, `email`, `intranet_uuid`

Manually managed fields (never touched by sync): `preferred_name`, `pronouns`, `date_of_birth`, `phone`, `educational_institution`, `is_flinta`, `barrier_free_needed`, `soli_miete_wunsch`, `move_in`, and all others.

---

## 8. Project Structure

```
cartei/
├── cartei/
│   ├── settings.py       # LDAP config (adapted from mattermost webui)
│   ├── urls.py
│   └── wsgi.py
├── app/
│   ├── models.py         # managed=False mirrors of cartei_db schema
│   ├── auth.py           # CustomLDAPBackend
│   ├── decorators.py     # require_group(*groups)
│   ├── views/
│   │   ├── abfragen.py
│   │   ├── tenants.py
│   │   └── admin.py      # LDAP sync
│   └── templates/
│       └── app/
├── Dockerfile            # mirrors mattermost webui Dockerfile (libldap-dev etc.)
├── gunicorn.conf.py
└── pyproject.toml
```

---

## 9. Out of Scope for MVP

- Move-in / move-out workflow (full tenant onboarding)
- Enrollment proof expiry notifications
- Room management UI
- Email notifications for AG engagement deadlines
- Tenant self-service profile editing
