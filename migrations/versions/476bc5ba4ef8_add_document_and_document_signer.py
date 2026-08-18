"""add per-type document tables and document_signer

Revision ID: 476bc5ba4ef8
Revises: 128b8d2e5a03
Create Date: 2026-08-17 17:42:52.997903

One table per document type (datenschutz_document, photoerlaubnis_document),
sharing an append-only trigger. A single polymorphic document_signer table
references any of them via (document_type, document_id).
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

from cartei_db.document_triggers import (
    document_append_only_sql,
    drop_document_append_only_sql,
)

# Snapshot of DOCUMENT_TABLES as of this migration — do not use the live tuple
# (new document tables added later have their own migrations).
_DOC_TABLES = ("datenschutz_document", "photoerlaubnis_document")


# revision identifiers, used by Alembic.
revision: str = '476bc5ba4ef8'
down_revision: Union[str, Sequence[str], None] = '128b8d2e5a03'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _create_document_table(name: str) -> None:
    op.create_table(
        name,
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


def upgrade() -> None:
    for table in _DOC_TABLES:
        _create_document_table(table)

    # Polymorphic signer: document_id has no FK (points at any document table).
    op.create_table(
        'document_signer',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('document_type', sa.String(length=50), nullable=False),
        sa.Column('document_id', sa.Integer(), nullable=False),
        sa.Column('tenant_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenant.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint(
            'document_type', 'document_id', 'tenant_id',
            name='uq_document_signer_doc_tenant',
        ),
    )

    op.drop_column('tenant', 'photo_allowance_signed_at')
    op.drop_column('tenant', 'data_priv_signed_at')

    for stmt in document_append_only_sql(_DOC_TABLES):
        op.execute(stmt)


def downgrade() -> None:
    for stmt in drop_document_append_only_sql(_DOC_TABLES):
        op.execute(stmt)

    op.add_column('tenant', sa.Column('data_priv_signed_at', sa.DATE(), nullable=True))
    op.add_column('tenant', sa.Column('photo_allowance_signed_at', sa.DATE(), nullable=True))

    op.drop_table('document_signer')
    for table in _DOC_TABLES:
        op.drop_table(table)
