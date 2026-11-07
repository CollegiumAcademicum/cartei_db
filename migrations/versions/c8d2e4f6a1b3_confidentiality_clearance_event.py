"""confidentiality clearance event approval log

Revision ID: c8d2e4f6a1b3
Revises: b7c1e2d3f4a5
Create Date: 2026-11-07 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

from cartei_db.clearance_triggers import (
    clearance_event_immutable_sql, drop_clearance_event_immutable_sql,
)


# revision identifiers, used by Alembic.
revision: str = 'c8d2e4f6a1b3'
down_revision: Union[str, Sequence[str], None] = 'b7c1e2d3f4a5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'confidentiality_clearance_event',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('tenant_id', sa.Integer(), nullable=False),
        sa.Column('document_id', sa.Integer(), nullable=False),
        sa.Column(
            'action', sa.Enum('GRANT', 'REGRANT', 'REVOKE', name='confidentialityclearanceaction'),
            nullable=False,
        ),
        sa.Column('actor_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenant.id']),
        sa.ForeignKeyConstraint(['document_id'], ['vertraulichkeitserklaerung_document.id']),
        sa.ForeignKeyConstraint(['actor_id'], ['tenant.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(
        op.f('ix_confidentiality_clearance_event_tenant_id'),
        'confidentiality_clearance_event', ['tenant_id'],
    )
    op.create_index(
        op.f('ix_confidentiality_clearance_event_document_id'),
        'confidentiality_clearance_event', ['document_id'],
    )
    # Backfill: every currently valid VE counts as an already-granted clearance
    # (actor NULL = legacy). The trigger is installed afterwards.
    op.execute(
        "INSERT INTO confidentiality_clearance_event "
        "(tenant_id, document_id, action, actor_id, created_at) "
        "SELECT tenant_id, id, 'GRANT', NULL, uploaded_at "
        "FROM vertraulichkeitserklaerung_document WHERE revoked_at IS NULL"
    )
    for stmt in clearance_event_immutable_sql():
        op.execute(stmt)


def downgrade() -> None:
    """Downgrade schema."""
    for stmt in drop_clearance_event_immutable_sql():
        op.execute(stmt)
    op.drop_index(op.f('ix_confidentiality_clearance_event_document_id'), table_name='confidentiality_clearance_event')
    op.drop_index(op.f('ix_confidentiality_clearance_event_tenant_id'), table_name='confidentiality_clearance_event')
    op.drop_table('confidentiality_clearance_event')
    sa.Enum(name='confidentialityclearanceaction').drop(op.get_bind())
