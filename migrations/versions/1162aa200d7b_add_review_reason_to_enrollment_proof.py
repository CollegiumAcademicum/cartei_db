"""add review_reason to enrollment_proof

Revision ID: 1162aa200d7b
Revises: b3c4d5e6f7a8
Create Date: 2026-08-15 01:00:35.796523

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '1162aa200d7b'
down_revision: Union[str, Sequence[str], None] = 'b3c4d5e6f7a8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('enrollment_proof', sa.Column('review_reason', sa.String(), nullable=True))


def downgrade() -> None:
    op.drop_column('enrollment_proof', 'review_reason')
