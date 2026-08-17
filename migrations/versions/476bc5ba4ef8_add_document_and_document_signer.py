"""add document and document_signer

Revision ID: 476bc5ba4ef8
Revises: 6b150084d2b1
Create Date: 2026-08-17 17:42:52.997903

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '476bc5ba4ef8'
down_revision: Union[str, Sequence[str], None] = '6b150084d2b1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('document',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('tenant_id', sa.Integer(), nullable=False),
    sa.Column('document_type', sa.Enum('datenschutz', 'photoerlaubnis', name='documenttype'), nullable=False),
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
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('document_signer',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('document_id', sa.Integer(), nullable=False),
    sa.Column('tenant_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['document_id'], ['document.id'], ),
    sa.ForeignKeyConstraint(['tenant_id'], ['tenant.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('document_id', 'tenant_id', name='uq_document_signer_document_tenant')
    )
    op.create_foreign_key(
        'enrollment_proof_uploaded_by_id_fkey',
        'enrollment_proof', 'tenant', ['uploaded_by_id'], ['id'],
    )
    op.create_foreign_key(
        'enrollment_proof_last_edited_by_id_fkey',
        'enrollment_proof', 'tenant', ['last_edited_by_id'], ['id'],
    )
    op.create_foreign_key(
        'enrollment_proof_verified_by_id_fkey',
        'enrollment_proof', 'tenant', ['verified_by_id'], ['id'],
    )
    op.drop_column('tenant', 'photo_allowance_signed_at')
    op.drop_column('tenant', 'data_priv_signed_at')

    from cartei_db.document_triggers import document_append_only_sql
    for stmt in document_append_only_sql():
        op.execute(stmt)


def downgrade() -> None:
    from cartei_db.document_triggers import drop_document_append_only_sql
    for stmt in drop_document_append_only_sql():
        op.execute(stmt)

    op.add_column('tenant', sa.Column('data_priv_signed_at', sa.DATE(), autoincrement=False, nullable=True))
    op.add_column('tenant', sa.Column('photo_allowance_signed_at', sa.DATE(), autoincrement=False, nullable=True))
    op.drop_constraint('enrollment_proof_verified_by_id_fkey', 'enrollment_proof', type_='foreignkey')
    op.drop_constraint('enrollment_proof_last_edited_by_id_fkey', 'enrollment_proof', type_='foreignkey')
    op.drop_constraint('enrollment_proof_uploaded_by_id_fkey', 'enrollment_proof', type_='foreignkey')
    op.drop_table('document_signer')
    op.drop_table('document')
    sa.Enum(name='documenttype').drop(op.get_bind())
