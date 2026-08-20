"""space OJ wg names: OJ1 -> OJ 1

Revision ID: a4b5c6d7e8f9
Revises: f3a04b4c5d6e
Create Date: 2026-08-20

Renames the Altbau OJ WGs from "OJ1".."OJ4" to "OJ 1".."OJ 4" (SWB/FWB
already carry the space).
"""
from typing import Sequence, Union

from alembic import op

revision: str = "a4b5c6d7e8f9"
down_revision: Union[str, Sequence[str], None] = "f3a04b4c5d6e"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(r"UPDATE wg SET name = 'OJ ' || substr(name, 3) WHERE name ~ '^OJ[0-9]'")


def downgrade() -> None:
    op.execute(r"UPDATE wg SET name = 'OJ' || substr(name, 4) WHERE name ~ '^OJ [0-9]'")
