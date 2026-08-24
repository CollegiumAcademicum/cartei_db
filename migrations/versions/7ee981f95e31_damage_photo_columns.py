"""damage photo columns

Revision ID: 7ee981f95e31
Revises: f69c41ec7771
Create Date: 2026-08-24 10:22:18.465218

Adds an optional single photo (photo_name + photo_data bytea) to room_damage
and wg_damage. Both NULL when absent; re-uploading replaces it.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '7ee981f95e31'
down_revision: Union[str, Sequence[str], None] = 'f69c41ec7771'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    for table in ("room_damage", "wg_damage"):
        op.add_column(table, sa.Column("photo_name", sa.Text(), nullable=True))
        op.add_column(table, sa.Column("photo_data", sa.LargeBinary(), nullable=True))


def downgrade() -> None:
    for table in ("room_damage", "wg_damage"):
        op.drop_column(table, "photo_data")
        op.drop_column(table, "photo_name")
