"""add audit triggers

Revision ID: 75b185c2506d
Revises: e3f4a5b6c7d8
Create Date: 2026-08-10 13:07:14.364623

"""
from typing import Sequence, Union

from alembic import op

from cartei_db.base import (
    AUDIT_FUNCTION_SQL, create_audit_trigger_sql, drop_audit_trigger_sql,
)

# revision identifiers, used by Alembic.
revision: str = '75b185c2506d'
down_revision: Union[str, Sequence[str], None] = 'e3f4a5b6c7d8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_AUDITED = {"tenant": {"is_flinta"}, "ag_abfrage_result": set(), "room": set()}


def upgrade() -> None:
    op.execute(AUDIT_FUNCTION_SQL)
    for table, exclude in _AUDITED.items():
        op.execute(create_audit_trigger_sql(table, exclude))


def downgrade() -> None:
    for table in _AUDITED:
        op.execute(drop_audit_trigger_sql(table))
    op.execute("DROP FUNCTION IF EXISTS audit_history() CASCADE")
