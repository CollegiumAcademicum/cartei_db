"""tenant.email_refreshed_at + audit skips excluded-column-only updates

Revision ID: b7c1e2d3f4a5
Revises: 6b2d9c3a1f04
Create Date: 2026-10-30 01:45:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

from cartei_db.base import AUDIT_FUNCTION_SQL, create_audit_trigger_sql

# revision identifiers, used by Alembic.
revision: str = 'b7c1e2d3f4a5'
down_revision: Union[str, Sequence[str], None] = '6b2d9c3a1f04'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# audit_history() as of 75b185c2506d, restored on downgrade.
_OLD_AUDIT_FUNCTION_SQL = """
CREATE OR REPLACE FUNCTION audit_history() RETURNS trigger AS $$
DECLARE
    snap jsonb;
    col  text;
BEGIN
    snap := to_jsonb(OLD);
    FOREACH col IN ARRAY coalesce(TG_ARGV, '{}') LOOP
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


def upgrade() -> None:
    """Email cache timestamp (FreeIPA is the email source of truth). Nullable,
    no backfill: existing rows were simply never confirmed. Bumping it alone must
    not write entity_history, so the audit function now skips UPDATEs that only
    change excluded columns, and tenant's trigger excludes the new column."""
    op.add_column('tenant', sa.Column('email_refreshed_at', sa.DateTime(timezone=True), nullable=True))
    op.execute(AUDIT_FUNCTION_SQL)
    op.execute(create_audit_trigger_sql('tenant', {'is_flinta', 'email_refreshed_at'}))


def downgrade() -> None:
    op.execute(create_audit_trigger_sql('tenant', {'is_flinta'}))
    op.execute(_OLD_AUDIT_FUNCTION_SQL)
    op.drop_column('tenant', 'email_refreshed_at')
