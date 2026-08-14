"""add cartei_vision role

Revision ID: 8381111cd9de
Revises: 1162aa200d7b
Create Date: 2026-08-15
"""
from alembic import op
from cartei_db.security import (
    CREATE_VISION_ROLE_SQL, grant_vision_sql, revoke_vision_sql, VISION_ROLE,
)

revision = "8381111cd9de"
down_revision = "1162aa200d7b"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(CREATE_VISION_ROLE_SQL)
    for stmt in grant_vision_sql():
        op.execute(stmt)


def downgrade() -> None:
    for stmt in revoke_vision_sql():
        op.execute(stmt)
    op.execute(f"DROP ROLE IF EXISTS {VISION_ROLE}")
