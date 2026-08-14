import os
import pytest
from sqlalchemy import create_engine, text

import cartei_db.models  # registers all models in Base.metadata before engine fixture runs
from cartei_db.security import (
    CREATE_VISION_ROLE_SQL, grant_vision_sql, revoke_vision_sql,
)


@pytest.fixture
def su_conn(engine):
    # engine fixture already created all tables; reuse its connection.
    conn = engine.connect()
    yield conn
    conn.close()


def _drop_vision_role(conn) -> None:
    """Drop cartei_vision and all its grants idempotently."""
    for stmt in revoke_vision_sql():
        try:
            conn.execute(text(stmt))
        except Exception:
            conn.rollback()
    conn.execute(text("DROP ROLE IF EXISTS cartei_vision"))
    conn.commit()


def test_role_and_grants_created_then_revoked(su_conn):
    # Clean up any leftover role from a prior aborted run (e.g. left by migration).
    _drop_vision_role(su_conn)

    su_conn.execute(text(CREATE_VISION_ROLE_SQL))
    for stmt in grant_vision_sql():
        su_conn.execute(text(stmt))
    su_conn.commit()

    role = su_conn.execute(text(
        "SELECT 1 FROM pg_roles WHERE rolname = 'cartei_vision'"
    )).scalar()
    assert role == 1

    # UPDATE granted on review_reason, NOT on file_data
    granted = su_conn.execute(text("""
        SELECT column_name FROM information_schema.role_column_grants
        WHERE grantee='cartei_vision' AND table_name='enrollment_proof'
          AND privilege_type='UPDATE'
    """)).scalars().all()
    assert 'review_reason' in granted
    assert 'verified_at' in granted
    assert 'file_data' not in granted

    _drop_vision_role(su_conn)
