"""move mietvertrag and mietbedingungen to tenant

Revision ID: 7684c61cd9a4
Revises: 048291eb22f5
Create Date: 2026-08-27 10:18:29.157443

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7684c61cd9a4'
down_revision: Union[str, Sequence[str], None] = '048291eb22f5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# Mietvertrag and Mietbedingungen move from per-assignment to per-tenant
# documents: re-key from tenant_room_assignment_id to tenant_id. Tables are empty
# (no rows to backfill). Wohnungsgeberbescheinigung stays per-assignment.
_TABLES = ("mietvertrag_document", "mietbedingungen_document")


def upgrade() -> None:
    """Upgrade schema."""
    for table in _TABLES:
        op.drop_constraint(f"{table}_tenant_room_assignment_id_fkey", table, type_="foreignkey")
        op.drop_column(table, "tenant_room_assignment_id")
        op.add_column(table, sa.Column("tenant_id", sa.Integer(), nullable=False))
        op.create_foreign_key(f"{table}_tenant_id_fkey", table, "tenant", ["tenant_id"], ["id"])


def downgrade() -> None:
    """Downgrade schema."""
    for table in _TABLES:
        op.drop_constraint(f"{table}_tenant_id_fkey", table, type_="foreignkey")
        op.drop_column(table, "tenant_id")
        op.add_column(table, sa.Column("tenant_room_assignment_id", sa.Integer(), nullable=False))
        op.create_foreign_key(
            f"{table}_tenant_room_assignment_id_fkey", table,
            "tenant_room_assignment", ["tenant_room_assignment_id"], ["id"],
        )
