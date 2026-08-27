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
# documents: re-key from tenant_room_assignment_id to tenant_id, backfilling each
# row from its assignment's tenant. Wohnungsgeberbescheinigung stays per-assignment.
_TABLES = ("mietvertrag_document", "mietbedingungen_document")


def upgrade() -> None:
    """Upgrade schema."""
    for table in _TABLES:
        # Add nullable first, backfill from the assignment's tenant, then enforce
        # NOT NULL. The backfill UPDATE must bypass the append-only trigger, which
        # otherwise rejects any update that isn't a revocation.
        op.add_column(table, sa.Column("tenant_id", sa.Integer(), nullable=True))
        op.execute(f"ALTER TABLE {table} DISABLE TRIGGER {table}_append_only")
        op.execute(
            f"UPDATE {table} AS d SET tenant_id = a.tenant_id "
            f"FROM tenant_room_assignment AS a WHERE a.id = d.tenant_room_assignment_id"
        )
        op.execute(f"ALTER TABLE {table} ENABLE TRIGGER {table}_append_only")
        op.alter_column(table, "tenant_id", nullable=False)
        op.create_foreign_key(f"{table}_tenant_id_fkey", table, "tenant", ["tenant_id"], ["id"])
        op.drop_constraint(f"{table}_tenant_room_assignment_id_fkey", table, type_="foreignkey")
        op.drop_column(table, "tenant_room_assignment_id")


def downgrade() -> None:
    """Downgrade schema."""
    for table in _TABLES:
        # Best-effort reverse: the original assignment is unrecoverable, so attach
        # each doc to the tenant's most recent assignment (by move-in date).
        op.add_column(table, sa.Column("tenant_room_assignment_id", sa.Integer(), nullable=True))
        op.execute(f"ALTER TABLE {table} DISABLE TRIGGER {table}_append_only")
        op.execute(
            f"UPDATE {table} AS d SET tenant_room_assignment_id = ("
            f"SELECT a.id FROM tenant_room_assignment AS a "
            f"WHERE a.tenant_id = d.tenant_id ORDER BY a.moved_in DESC LIMIT 1)"
        )
        op.execute(f"ALTER TABLE {table} ENABLE TRIGGER {table}_append_only")
        op.alter_column(table, "tenant_room_assignment_id", nullable=False)
        op.create_foreign_key(
            f"{table}_tenant_room_assignment_id_fkey", table,
            "tenant_room_assignment", ["tenant_room_assignment_id"], ["id"],
        )
        op.drop_constraint(f"{table}_tenant_id_fkey", table, type_="foreignkey")
        op.drop_column(table, "tenant_id")
