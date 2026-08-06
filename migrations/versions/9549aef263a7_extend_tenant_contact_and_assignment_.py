"""extend tenant contact and assignment fields

Revision ID: 9549aef263a7
Revises: 4cc588f5d460
Create Date: 2026-08-05 15:56:24.008250

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '9549aef263a7'
down_revision: Union[str, Sequence[str], None] = '4cc588f5d460'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('tenant', sa.Column('preferred_name', sa.String(), nullable=True))
    op.add_column('tenant', sa.Column('pronouns', sa.String(), nullable=True))
    op.add_column('tenant', sa.Column('date_of_birth', sa.Date(), nullable=True))
    op.add_column('tenant', sa.Column('phone', sa.String(), nullable=True))
    op.add_column('tenant', sa.Column('educational_institution', sa.String(), nullable=True))
    op.add_column('tenant', sa.Column('data_priv_signed_at', sa.Date(), nullable=True))
    op.add_column('tenant', sa.Column('photo_allowance_signed_at', sa.Date(), nullable=True))
    op.add_column('tenant_room_assignment', sa.Column('key_handed_over', sa.Boolean(), nullable=False, server_default='false'))
    op.alter_column('tenant_room_assignment', 'key_handed_over', server_default=None)
    op.add_column('tenant_room_assignment', sa.Column('deposit_iban', sa.String(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('tenant_room_assignment', 'deposit_iban')
    op.drop_column('tenant_room_assignment', 'key_handed_over')
    op.drop_column('tenant', 'photo_allowance_signed_at')
    op.drop_column('tenant', 'data_priv_signed_at')
    op.drop_column('tenant', 'educational_institution')
    op.drop_column('tenant', 'phone')
    op.drop_column('tenant', 'date_of_birth')
    op.drop_column('tenant', 'pronouns')
    op.drop_column('tenant', 'preferred_name')
