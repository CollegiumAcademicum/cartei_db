"""tenant locale

Revision ID: f1a2b3c4d5e6
Revises: e5f8b1c3d2a4
Create Date: 2026-11-18 17:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f1a2b3c4d5e6'
down_revision: Union[str, Sequence[str], None] = 'e5f8b1c3d2a4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Nullable, no backfill: existing tenants stay unknown until their next login.
    op.add_column('tenant', sa.Column('locale', sa.String(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('tenant', 'locale')
