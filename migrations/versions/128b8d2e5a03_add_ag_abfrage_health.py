"""add ag_abfrage_health

Revision ID: 128b8d2e5a03
Revises: 6b150084d2b1
Create Date: 2026-08-17 03:49:27.744530

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

from cartei_db.base import create_audit_trigger_sql, drop_audit_trigger_sql


# revision identifiers, used by Alembic.
revision: str = '128b8d2e5a03'
down_revision: Union[str, Sequence[str], None] = '6b150084d2b1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('ag_abfrage_health',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('abfrage_id', sa.Integer(), nullable=False),
    sa.Column('ag_name', sa.String(), nullable=False),
    sa.Column('health', sa.Enum('GESUND', 'KERNAUFGABEN', 'KRITISCH', 'TOT', name='aghealth'), nullable=False),
    sa.Column('note', sa.Text(), nullable=True),
    sa.ForeignKeyConstraint(['abfrage_id'], ['ag_abfrage.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('abfrage_id', 'ag_name', name='uq_ag_abfrage_health')
    )
    op.execute(create_audit_trigger_sql('ag_abfrage_health', set()))


def downgrade() -> None:
    op.execute(drop_audit_trigger_sql('ag_abfrage_health'))
    op.drop_table('ag_abfrage_health')
    sa.Enum(name='aghealth').drop(op.get_bind())
