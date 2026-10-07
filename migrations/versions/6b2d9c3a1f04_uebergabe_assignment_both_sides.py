"""uebergabe: link outgoing + incoming assignments (drop incoming_tenant)

Revision ID: 6b2d9c3a1f04
Revises: 521958efded7
Create Date: 2026-10-08 01:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '6b2d9c3a1f04'
down_revision: Union[str, Sequence[str], None] = '521958efded7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """A handover links two assignments of its room. Outgoing is the renamed
    original column; incoming becomes an assignment FK (was a tenant FK)."""
    op.alter_column('uebergabe', 'tenant_room_assignment_id',
                    new_column_name='outgoing_assignment_id')
    op.drop_constraint('fk_uebergabe_incoming_tenant_id_tenant', 'uebergabe', type_='foreignkey')
    op.drop_column('uebergabe', 'incoming_tenant_id')
    op.add_column('uebergabe', sa.Column('incoming_assignment_id', sa.Integer(), nullable=True))
    op.create_foreign_key('fk_uebergabe_incoming_assignment', 'uebergabe',
                          'tenant_room_assignment', ['incoming_assignment_id'], ['id'])


def downgrade() -> None:
    op.drop_constraint('fk_uebergabe_incoming_assignment', 'uebergabe', type_='foreignkey')
    op.drop_column('uebergabe', 'incoming_assignment_id')
    op.add_column('uebergabe', sa.Column('incoming_tenant_id', sa.Integer(), nullable=True))
    op.create_foreign_key('fk_uebergabe_incoming_tenant_id_tenant', 'uebergabe',
                          'tenant', ['incoming_tenant_id'], ['id'])
    op.alter_column('uebergabe', 'outgoing_assignment_id',
                    new_column_name='tenant_room_assignment_id')
