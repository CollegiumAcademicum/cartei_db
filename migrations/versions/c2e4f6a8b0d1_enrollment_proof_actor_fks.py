"""enrollment_proof actor FKs

Revision ID: c2e4f6a8b0d1
Revises: b1f3a9c2d4e5
Create Date: 2026-08-28 12:15:00.000000

The enrollment_proof redesign (b3c4d5e6f7a8) added uploaded_by_id /
verified_by_id / last_edited_by_id as plain integers but never emitted the
FK constraints the models declare. Add them now. NOT VALID first (cheap,
no full-table scan under lock) then VALIDATE (scans without blocking writes)
so this is safe on the deployed, non-empty table.
"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = 'c2e4f6a8b0d1'
down_revision: Union[str, Sequence[str], None] = 'b1f3a9c2d4e5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_ACTOR_COLS = ["uploaded_by_id", "verified_by_id", "last_edited_by_id"]


def _fk_name(col: str) -> str:
    return f"enrollment_proof_{col}_fkey"


def upgrade() -> None:
    for col in _ACTOR_COLS:
        name = _fk_name(col)
        op.execute(
            f"ALTER TABLE enrollment_proof ADD CONSTRAINT {name} "
            f"FOREIGN KEY ({col}) REFERENCES tenant (id) NOT VALID"
        )
        op.execute(f"ALTER TABLE enrollment_proof VALIDATE CONSTRAINT {name}")


def downgrade() -> None:
    for col in _ACTOR_COLS:
        op.execute(f"ALTER TABLE enrollment_proof DROP CONSTRAINT {_fk_name(col)}")
