"""engagement_and_cluster_note

Revision ID: 8b848a567437
Revises: 9549aef263a7
Create Date: 2026-08-05 22:25:56.858596

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '8b848a567437'
down_revision: Union[str, Sequence[str], None] = '9549aef263a7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ag_abfrage: add ends_at and grace_ends_at (NOT NULL, temp default covers existing rows)
    op.add_column("ag_abfrage", sa.Column("ends_at", sa.Date(), nullable=False,
                  server_default=sa.text("CURRENT_DATE")))
    op.add_column("ag_abfrage", sa.Column("grace_ends_at", sa.Date(), nullable=False,
                  server_default=sa.text("CURRENT_DATE + INTERVAL '7 days'")))
    op.alter_column("ag_abfrage", "ends_at", server_default=None)
    op.alter_column("ag_abfrage", "grace_ends_at", server_default=None)

    # ag_abfrage_result: add optional note
    op.add_column("ag_abfrage_result", sa.Column("note", sa.Text(), nullable=True))

    # tenant: make move_in nullable; add server_default to is_flinta
    op.alter_column("tenant", "move_in", nullable=True,
                    existing_type=sa.Date())
    op.alter_column("tenant", "is_flinta", server_default=sa.text("false"),
                    existing_type=sa.Boolean(), existing_nullable=False)

    # cluster_note: new table
    op.create_table(
        "cluster_note",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("tenant_id", sa.Integer(), sa.ForeignKey("tenant.id"), nullable=False),
        sa.Column("abfrage_id", sa.Integer(), sa.ForeignKey("ag_abfrage.id"), nullable=False),
        sa.Column("note", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_by", sa.String(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("cluster_note")
    op.alter_column("tenant", "is_flinta", server_default=None,
                    existing_type=sa.Boolean(), existing_nullable=False)
    op.alter_column("tenant", "move_in", nullable=False, existing_type=sa.Date())
    op.drop_column("ag_abfrage_result", "note")
    op.drop_column("ag_abfrage", "grace_ends_at")
    op.drop_column("ag_abfrage", "ends_at")
