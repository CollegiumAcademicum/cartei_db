"""split mailbox_key into received/returned dates

Revision ID: a7f3c9d21e40
Revises: d69d4eb566ce
Create Date: 2026-08-16 15:33:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a7f3c9d21e40'
down_revision: Union[str, Sequence[str], None] = 'd69d4eb566ce'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('tenant_room_assignment', sa.Column('mailbox_key_received', sa.Date(), nullable=True))
    op.add_column('tenant_room_assignment', sa.Column('mailbox_key_returned', sa.Date(), nullable=True))
    op.drop_column('tenant_room_assignment', 'mailbox_key')


def downgrade() -> None:
    """Downgrade schema."""
    op.add_column('tenant_room_assignment', sa.Column('mailbox_key', sa.BOOLEAN(), server_default='false', autoincrement=False, nullable=False))
    op.drop_column('tenant_room_assignment', 'mailbox_key_returned')
    op.drop_column('tenant_room_assignment', 'mailbox_key_received')
