"""add tenant finance documents

Revision ID: a77d2242c27c
Revises: 7684c61cd9a4
Create Date: 2026-08-27 11:20:23.507025

Three more per-tenant document tables (SEPA-Lastschriftmandat with its
structured mandate fields, Bescheid für Ausbildungsstellen with a CA-side
signer, and Selbstverpflichtung Engagement), same append-only shape as the
existing consent documents.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

from cartei_db.document_triggers import document_append_only_sql


# revision identifiers, used by Alembic.
revision: str = 'a77d2242c27c'
down_revision: Union[str, Sequence[str], None] = '7684c61cd9a4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _base_columns() -> list:
    """The shared DocumentColumns shape (incl. signed_at)."""
    return [
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('tenant_id', sa.Integer(), nullable=False),
        sa.Column('file_name', sa.String(), nullable=False),
        sa.Column('file_data', sa.LargeBinary(), nullable=False),
        sa.Column('signed_at', sa.Date(), nullable=False),
        sa.Column('uploaded_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('uploaded_by_id', sa.Integer(), nullable=False),
        sa.Column('revoked_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('revoked_by_id', sa.Integer(), nullable=True),
        sa.Column('revoked_note', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['revoked_by_id'], ['tenant.id'], ),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenant.id'], ),
        sa.ForeignKeyConstraint(['uploaded_by_id'], ['tenant.id'], ),
        sa.PrimaryKeyConstraint('id'),
    ]


_TABLES = (
    "sepa_lastschriftmandat_document",
    "bescheid_ausbildungsstelle_document",
    "selbstverpflichtung_engagement_document",
)


def upgrade() -> None:
    op.create_table(
        "sepa_lastschriftmandat_document",
        *_base_columns(),
        sa.Column('mandatsreferenz', sa.String(), nullable=False),
        sa.Column('kontoinhaber', sa.String(), nullable=False),
        sa.Column('bank_name', sa.String(), nullable=False),
        sa.Column('iban', sa.String(), nullable=False),
        sa.Column('bic', sa.String(), nullable=False),
    )
    op.create_table(
        "bescheid_ausbildungsstelle_document",
        *_base_columns(),
        sa.Column('signed_by_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['signed_by_id'], ['tenant.id'], ),
    )
    op.create_table(
        "selbstverpflichtung_engagement_document",
        *_base_columns(),
    )
    # CREATE OR REPLACE FUNCTION + trigger for the new tables only.
    for stmt in document_append_only_sql(_TABLES):
        op.execute(stmt)


def downgrade() -> None:
    for table in _TABLES:
        op.execute(f"DROP TRIGGER IF EXISTS {table}_append_only ON {table}")
        op.drop_table(table)
