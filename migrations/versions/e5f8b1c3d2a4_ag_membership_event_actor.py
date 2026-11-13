"""ag membership event actor and nullable tenant

Revision ID: e5f8b1c3d2a4
Revises: d4e7a9b2c1f0
Create Date: 2026-11-13 13:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

from cartei_db.ag_membership_triggers import (
    ag_membership_event_immutable_sql, drop_ag_membership_event_immutable_sql,
)


# revision identifiers, used by Alembic.
revision: str = 'e5f8b1c3d2a4'
down_revision: Union[str, Sequence[str], None] = 'd4e7a9b2c1f0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('ag_membership_event', sa.Column('actor_username', sa.Text(), nullable=True))
    # Existing rows are all dashboard self-service: the actor is the member.
    # The append-only trigger would reject the backfill, so lift it around it.
    for stmt in drop_ag_membership_event_immutable_sql():
        op.execute(stmt)
    op.execute("UPDATE ag_membership_event SET actor_username = uid")
    for stmt in ag_membership_event_immutable_sql():
        op.execute(stmt)
    op.alter_column('ag_membership_event', 'actor_username', nullable=False)
    op.alter_column('ag_membership_event', 'tenant_id', existing_type=sa.Integer(), nullable=True)


def downgrade() -> None:
    """Downgrade schema."""
    for stmt in drop_ag_membership_event_immutable_sql():
        op.execute(stmt)
    op.execute("DELETE FROM ag_membership_event WHERE tenant_id IS NULL")
    for stmt in ag_membership_event_immutable_sql():
        op.execute(stmt)
    op.alter_column('ag_membership_event', 'tenant_id', existing_type=sa.Integer(), nullable=False)
    op.drop_column('ag_membership_event', 'actor_username')
