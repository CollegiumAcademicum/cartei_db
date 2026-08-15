"""SQL for the least-privilege `cartei_vision` worker role.

Grants are column-scoped so a leaked credential can only read a proof PDF +
tenant names and flip verification columns. Password is set out of band by
cartei_deployment; the migration creates the role without one.
"""

VISION_ROLE = "cartei_vision"

# Idempotent: roles are cluster-global and CREATE ROLE has no IF NOT EXISTS.
CREATE_VISION_ROLE_SQL = f"""
DO $$ BEGIN
  IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = '{VISION_ROLE}') THEN
    CREATE ROLE {VISION_ROLE} LOGIN;  -- password set by deployment, not here
  END IF;
END $$;
"""

_UPDATE_COLS = (
    "verified_at, verified_by_id, enrollment_type, field_of_study, "
    "educational_institution, valid_until, needs_human_review, review_reason"
)


def grant_vision_sql() -> list[str]:
    """Return individual GRANT statements (psycopg3 rejects multi-statement strings)."""
    return [
        f"GRANT USAGE ON SCHEMA public TO {VISION_ROLE}",
        f"GRANT SELECT ON enrollment_proof TO {VISION_ROLE}",
        f"GRANT SELECT (id, first_name, last_name) ON tenant TO {VISION_ROLE}",
        f"GRANT UPDATE ({_UPDATE_COLS}) ON enrollment_proof TO {VISION_ROLE}",
    ]


def revoke_vision_sql() -> list[str]:
    """Return individual REVOKE statements (psycopg3 rejects multi-statement strings)."""
    return [
        f"REVOKE ALL ON enrollment_proof FROM {VISION_ROLE}",
        f"REVOKE ALL (id, first_name, last_name) ON tenant FROM {VISION_ROLE}",
        f"REVOKE USAGE ON SCHEMA public FROM {VISION_ROLE}",
    ]
