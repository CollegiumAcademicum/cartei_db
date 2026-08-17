"""add vertraulichkeitserklaerung_document

Revision ID: 2c2fe32a98a7
Revises: 476bc5ba4ef8
Create Date: 2026-08-17 21:46:52.572658

Third per-type document table (Vertraulichkeitserklärung), same shape as
datenschutz_document/photoerlaubnis_document and carrying the shared
append-only trigger.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

from cartei_db.document_triggers import document_append_only_sql


# revision identifiers, used by Alembic.
revision: str = '2c2fe32a98a7'
down_revision: Union[str, Sequence[str], None] = '476bc5ba4ef8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_TABLE = "vertraulichkeitserklaerung_document"


def upgrade() -> None:
    op.create_table(
        _TABLE,
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('tenant_id', sa.Integer(), nullable=False),
        sa.Column('file_name', sa.String(), nullable=False),
        sa.Column('file_data', sa.LargeBinary(), nullable=False),
        sa.Column('signed_at', sa.Date(), nullable=False),
        sa.Column('uploaded_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('uploaded_by_id', sa.Integer(), nullable=False),
        sa.Column('revoked_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('revoked_by_id', sa.Integer(), nullable=True),
        sa.Column('revoked_note', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['revoked_by_id'], ['tenant.id'], ),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenant.id'], ),
        sa.ForeignKeyConstraint(['uploaded_by_id'], ['tenant.id'], ),
        sa.PrimaryKeyConstraint('id'),
    )
    # CREATE OR REPLACE FUNCTION + trigger for the new table only.
    for stmt in document_append_only_sql((_TABLE,)):
        op.execute(stmt)


def downgrade() -> None:
    # Drop only this table's trigger; the shared function stays for the others.
    op.execute(f"DROP TRIGGER IF EXISTS {_TABLE}_append_only ON {_TABLE}")
    op.drop_table(_TABLE)
