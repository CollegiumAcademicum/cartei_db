"""impersonation event audit log

Revision ID: a7e3c1f09b42
Revises: d6f2a8c9e401
Create Date: 2026-10-06 00:10:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

from cartei_db.impersonation_triggers import (
    impersonation_event_immutable_sql, drop_impersonation_event_immutable_sql,
)


# revision identifiers, used by Alembic.
revision: str = 'a7e3c1f09b42'
down_revision: Union[str, Sequence[str], None] = 'd6f2a8c9e401'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'impersonation_event',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('impersonator_username', sa.String(length=150), nullable=False),
        sa.Column('target_username', sa.String(length=150), nullable=False),
        sa.Column('action', sa.Enum('START', 'STOP', name='impersonationaction'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(
        op.f('ix_impersonation_event_impersonator_username'),
        'impersonation_event', ['impersonator_username'],
    )
    op.create_index(
        op.f('ix_impersonation_event_target_username'),
        'impersonation_event', ['target_username'],
    )
    for stmt in impersonation_event_immutable_sql():
        op.execute(stmt)


def downgrade() -> None:
    """Downgrade schema."""
    for stmt in drop_impersonation_event_immutable_sql():
        op.execute(stmt)
    op.drop_index(op.f('ix_impersonation_event_target_username'), table_name='impersonation_event')
    op.drop_index(op.f('ix_impersonation_event_impersonator_username'), table_name='impersonation_event')
    op.drop_table('impersonation_event')
    sa.Enum(name='impersonationaction').drop(op.get_bind())
