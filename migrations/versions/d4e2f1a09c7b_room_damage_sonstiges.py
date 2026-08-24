"""room damage sonstiges line

Revision ID: d4e2f1a09c7b
Revises: 7ee981f95e31
Create Date: 2026-08-24 12:45:00.000000

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = 'd4e2f1a09c7b'
down_revision: Union[str, Sequence[str], None] = '7ee981f95e31'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("ALTER TYPE roomdamageline ADD VALUE IF NOT EXISTS 'SONSTIGES'")


def downgrade() -> None:
    # Postgres cannot drop a single enum value; leaving it in place is harmless.
    pass
