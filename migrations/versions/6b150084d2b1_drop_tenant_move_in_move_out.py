"""drop tenant move_in/move_out (now computed from room assignments)

Revision ID: 6b150084d2b1
Revises: a7f3c9d21e40
Create Date: 2026-08-17 02:59:23.929706

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '6b150084d2b1'
down_revision: Union[str, Sequence[str], None] = 'a7f3c9d21e40'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_column("tenant", "move_in")
    op.drop_column("tenant", "move_out")


def downgrade() -> None:
    op.add_column("tenant", sa.Column("move_out", sa.Date(), nullable=True))
    op.add_column("tenant", sa.Column("move_in", sa.Date(), nullable=True))
