"""unique constraint on ag_abfrage_result

Revision ID: a1b2c3d4e5f6
Revises: 8b848a567437
Create Date: 2026-08-08 14:23:00.000000

"""
from typing import Sequence, Union

from alembic import op

revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, Sequence[str], None] = "8b848a567437"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_unique_constraint(
        "uq_ag_abfrage_result",
        "ag_abfrage_result",
        ["abfrage_id", "ag_name", "tenant_id"],
    )


def downgrade() -> None:
    op.drop_constraint("uq_ag_abfrage_result", "ag_abfrage_result", type_="unique")