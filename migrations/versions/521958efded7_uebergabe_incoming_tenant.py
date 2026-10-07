"""uebergabe_incoming_tenant

Revision ID: 521958efded7
Revises: 5e6297a8ef91
Create Date: 2026-10-08 00:08:15.605929

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '521958efded7'
down_revision: Union[str, Sequence[str], None] = '5e6297a8ef91'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add the moving-in tenant to a room handover."""
    op.add_column('uebergabe', sa.Column('incoming_tenant_id', sa.Integer(), nullable=True))
    op.create_foreign_key(
        'fk_uebergabe_incoming_tenant_id_tenant',
        'uebergabe', 'tenant', ['incoming_tenant_id'], ['id'])


def downgrade() -> None:
    op.drop_constraint('fk_uebergabe_incoming_tenant_id_tenant', 'uebergabe', type_='foreignkey')
    op.drop_column('uebergabe', 'incoming_tenant_id')
