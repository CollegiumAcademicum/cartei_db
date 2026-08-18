"""room assignment documents

Revision ID: 7ae6942f6d70
Revises: 2c2fe32a98a7
Create Date: 2026-08-18 00:48:08.972677

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

from cartei_db.document_triggers import document_append_only_sql

# revision identifiers, used by Alembic.
revision: str = '7ae6942f6d70'
down_revision: Union[str, Sequence[str], None] = '2c2fe32a98a7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_NEW_DOC_TABLES = (
    "mietvertrag_document",
    "mietbedingungen_document",
    "wohnungsgeberbescheinigung_document",
)


def upgrade() -> None:
    op.create_table('mietbedingungen_document',
    sa.Column('signed_at', sa.Date(), nullable=False),
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('tenant_room_assignment_id', sa.Integer(), nullable=False),
    sa.Column('file_name', sa.String(), nullable=False),
    sa.Column('file_data', sa.LargeBinary(), nullable=False),
    sa.Column('uploaded_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('uploaded_by_id', sa.Integer(), nullable=False),
    sa.Column('revoked_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('revoked_by_id', sa.Integer(), nullable=True),
    sa.Column('revoked_note', sa.Text(), nullable=True),
    sa.ForeignKeyConstraint(['revoked_by_id'], ['tenant.id'], ),
    sa.ForeignKeyConstraint(['tenant_room_assignment_id'], ['tenant_room_assignment.id'], ),
    sa.ForeignKeyConstraint(['uploaded_by_id'], ['tenant.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('mietvertrag_document',
    sa.Column('renter_signed_at', sa.Date(), nullable=False),
    sa.Column('company_signed_at', sa.Date(), nullable=False),
    sa.Column('company_signed_by_id', sa.Integer(), nullable=False),
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('tenant_room_assignment_id', sa.Integer(), nullable=False),
    sa.Column('file_name', sa.String(), nullable=False),
    sa.Column('file_data', sa.LargeBinary(), nullable=False),
    sa.Column('uploaded_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('uploaded_by_id', sa.Integer(), nullable=False),
    sa.Column('revoked_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('revoked_by_id', sa.Integer(), nullable=True),
    sa.Column('revoked_note', sa.Text(), nullable=True),
    sa.ForeignKeyConstraint(['company_signed_by_id'], ['tenant.id'], ),
    sa.ForeignKeyConstraint(['revoked_by_id'], ['tenant.id'], ),
    sa.ForeignKeyConstraint(['tenant_room_assignment_id'], ['tenant_room_assignment.id'], ),
    sa.ForeignKeyConstraint(['uploaded_by_id'], ['tenant.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('wohnungsgeberbescheinigung_document',
    sa.Column('signed_at', sa.Date(), nullable=False),
    sa.Column('company_signed_by_id', sa.Integer(), nullable=False),
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('tenant_room_assignment_id', sa.Integer(), nullable=False),
    sa.Column('file_name', sa.String(), nullable=False),
    sa.Column('file_data', sa.LargeBinary(), nullable=False),
    sa.Column('uploaded_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('uploaded_by_id', sa.Integer(), nullable=False),
    sa.Column('revoked_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('revoked_by_id', sa.Integer(), nullable=True),
    sa.Column('revoked_note', sa.Text(), nullable=True),
    sa.ForeignKeyConstraint(['company_signed_by_id'], ['tenant.id'], ),
    sa.ForeignKeyConstraint(['revoked_by_id'], ['tenant.id'], ),
    sa.ForeignKeyConstraint(['tenant_room_assignment_id'], ['tenant_room_assignment.id'], ),
    sa.ForeignKeyConstraint(['uploaded_by_id'], ['tenant.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    for stmt in document_append_only_sql(_NEW_DOC_TABLES):
        op.execute(stmt)


def downgrade() -> None:
    # Drop only this migration's triggers; the shared function stays as long as
    # earlier document tables still have triggers depending on it.
    for table in _NEW_DOC_TABLES:
        op.execute(f"DROP TRIGGER IF EXISTS {table}_append_only ON {table}")
    op.drop_table('wohnungsgeberbescheinigung_document')
    op.drop_table('mietvertrag_document')
    op.drop_table('mietbedingungen_document')
