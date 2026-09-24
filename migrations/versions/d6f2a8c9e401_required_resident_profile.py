"""Track explicit resident profile setup and the no-phone choice.

Revision ID: d6f2a8c9e401
Revises: c2e4f6a8b0d1
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "d6f2a8c9e401"
down_revision: Union[str, Sequence[str], None] = "c2e4f6a8b0d1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("tenant", sa.Column("profile_setup_completed_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("tenant", sa.Column("no_phone_number", sa.Boolean(), server_default=sa.false(), nullable=False))


def downgrade() -> None:
    op.drop_column("tenant", "no_phone_number")
    op.drop_column("tenant", "profile_setup_completed_at")
