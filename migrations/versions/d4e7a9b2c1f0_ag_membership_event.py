"""ag membership event log

Revision ID: d4e7a9b2c1f0
Revises: c8d2e4f6a1b3
Create Date: 2026-11-13 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

from cartei_db.ag_membership_triggers import (
    ag_membership_event_immutable_sql, drop_ag_membership_event_immutable_sql,
)


# revision identifiers, used by Alembic.
revision: str = 'd4e7a9b2c1f0'
down_revision: Union[str, Sequence[str], None] = 'c8d2e4f6a1b3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'ag_membership_event',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('tenant_id', sa.Integer(), nullable=False),
        sa.Column('uid', sa.Text(), nullable=False),
        sa.Column('group_cn', sa.Text(), nullable=False),
        sa.Column('action', sa.Enum('JOIN', 'LEAVE', name='agmembershipaction'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenant.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_ag_membership_event_tenant_id'), 'ag_membership_event', ['tenant_id'])
    op.create_index(op.f('ix_ag_membership_event_group_cn'), 'ag_membership_event', ['group_cn'])
    for stmt in ag_membership_event_immutable_sql():
        op.execute(stmt)


def downgrade() -> None:
    """Downgrade schema."""
    for stmt in drop_ag_membership_event_immutable_sql():
        op.execute(stmt)
    op.drop_index(op.f('ix_ag_membership_event_group_cn'), table_name='ag_membership_event')
    op.drop_index(op.f('ix_ag_membership_event_tenant_id'), table_name='ag_membership_event')
    op.drop_table('ag_membership_event')
    sa.Enum(name='agmembershipaction').drop(op.get_bind())
