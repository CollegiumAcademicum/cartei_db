"""user_session table

Revision ID: 048291eb22f5
Revises: d4e2f1a09c7b
Create Date: 2026-08-26 22:11:50.720104

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '048291eb22f5'
down_revision: Union[str, Sequence[str], None] = 'd4e2f1a09c7b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "user_session",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("session_key", sa.String(length=40), nullable=False),
        sa.Column("username", sa.String(length=150), nullable=False),
        sa.Column("ip_address", sa.String(length=45), nullable=True),
        sa.Column("user_agent", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("session_key", name="uq_user_session_session_key"),
    )
    op.create_index("ix_user_session_username", "user_session", ["username"])


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index("ix_user_session_username", table_name="user_session")
    op.drop_table("user_session")
