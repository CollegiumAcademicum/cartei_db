"""wg_cluster

Revision ID: d2e3f4a5b6c7
Revises: c1d2e3f4a5b6
Create Date: 2026-08-08

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "d2e3f4a5b6c7"
down_revision: Union[str, Sequence[str], None] = "c1d2e3f4a5b6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_VALID = ("0A", "0B", "1A", "1B", "1C", "1D", "2A", "2B", "2C", "2D", "3A", "3B", "3C", "3D")


def upgrade() -> None:
    op.add_column("wg", sa.Column("cluster", sa.String(3), nullable=True))
    op.create_check_constraint(
        "wg_cluster_valid",
        "wg",
        f"cluster IN ({', '.join(repr(c) for c in _VALID)})",
    )


def downgrade() -> None:
    op.drop_constraint("wg_cluster_valid", "wg", type_="check")
    op.drop_column("wg", "cluster")