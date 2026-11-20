"""tenant_room_assignment writes entity_history

Revision ID: a1d9c4e7b2f3
Revises: f1a2b3c4d5e6
Create Date: 2026-11-20 15:30:00.000000

"""
from typing import Sequence, Union

from alembic import op

from cartei_db.base import create_audit_trigger_sql, drop_audit_trigger_sql

# revision identifiers, used by Alembic.
revision: str = 'a1d9c4e7b2f3'
down_revision: Union[str, Sequence[str], None] = 'f1a2b3c4d5e6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Assignments are edited in place (move-out, keys, sublet, deposit IBAN), so
    every UPDATE/DELETE now snapshots the old row, IBAN included (CArtei#115:
    the timeline shows it only to roles that may see it). Trigger only, no data
    change: edits before this revision stay unrecorded."""
    op.execute(create_audit_trigger_sql('tenant_room_assignment'))


def downgrade() -> None:
    op.execute(drop_audit_trigger_sql('tenant_room_assignment'))
