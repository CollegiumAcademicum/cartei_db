"""internal_note

Revision ID: f75ce2e5f513
Revises: 62e2fb604de4
Create Date: 2026-08-12 23:59:14.228048

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'f75ce2e5f513'
down_revision: Union[str, Sequence[str], None] = '62e2fb604de4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "internal_note",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("source_group", sa.String(50), nullable=False),
        sa.Column("subject_type", sa.String(50), nullable=False),
        sa.Column("subject_id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_by_id", sa.Integer(), sa.ForeignKey("tenant.id"), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("deleted_by_id", sa.Integer(), sa.ForeignKey("tenant.id"), nullable=True),
    )
    # Migrate existing cluster_note rows; skip rows whose username has no matching tenant.
    op.get_bind().execute(sa.text("""
        INSERT INTO internal_note
            (body, source_group, subject_type, subject_id, created_at, created_by_id)
        SELECT cn.note, 'clustersprechende', 'tenant', cn.tenant_id, cn.created_at, t.id
        FROM cluster_note cn
        JOIN tenant t ON t.intranet_username = cn.created_by
    """))
    op.drop_table("cluster_note")


def downgrade() -> None:
    op.create_table(
        "cluster_note",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("tenant_id", sa.Integer(), sa.ForeignKey("tenant.id"), nullable=False),
        sa.Column("abfrage_id", sa.Integer(), sa.ForeignKey("ag_abfrage.id"), nullable=False),
        sa.Column("note", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_by", sa.String(), nullable=False),
    )
    op.drop_table("internal_note")
