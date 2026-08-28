"""tenant ldap link nullable

Revision ID: b1f3a9c2d4e5
Revises: a77d2242c27c
Create Date: 2026-08-28 11:56:00.000000

Allow Mietverwaltung to add tenants manually before an intranet account exists:
intranet_username / intranet_uuid become nullable. The unique constraints stay
(Postgres treats each NULL as distinct, so many account-less tenants coexist).
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b1f3a9c2d4e5'
down_revision: Union[str, Sequence[str], None] = 'a77d2242c27c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column('tenant', 'intranet_username', existing_type=sa.String(), nullable=True)
    op.alter_column('tenant', 'intranet_uuid', existing_type=sa.Uuid(), nullable=True)


def downgrade() -> None:
    op.alter_column('tenant', 'intranet_uuid', existing_type=sa.Uuid(), nullable=False)
    op.alter_column('tenant', 'intranet_username', existing_type=sa.String(), nullable=False)
