"""enrollment_proof redesign: audit trail, new enum values, drop redundant tenant fields

Revision ID: b3c4d5e6f7a8
Revises: f75ce2e5f513
Create Date: 2026-08-13

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = 'b3c4d5e6f7a8'
down_revision: Union[str, Sequence[str], None] = 'f75ce2e5f513'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add new enum values (must precede column operations that use the type)
    op.execute("ALTER TYPE enrollmenttype ADD VALUE IF NOT EXISTS 'SCHUELER'")
    op.execute("ALTER TYPE enrollmenttype ADD VALUE IF NOT EXISTS 'FSJ'")

    # Rename columns
    op.alter_column('enrollment_proof', 'enrollment_name', new_column_name='field_of_study')
    op.alter_column('enrollment_proof', 'submitted_at', new_column_name='uploaded_at')

    # Add new columns (FKs added separately per project pattern)
    op.add_column('enrollment_proof', sa.Column('educational_institution', sa.String(), nullable=True))
    op.add_column('enrollment_proof', sa.Column('uploaded_by_id', sa.Integer(), nullable=True))
    op.add_column('enrollment_proof', sa.Column('last_edited_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('enrollment_proof', sa.Column('last_edited_by_id', sa.Integer(), nullable=True))
    op.add_column('enrollment_proof', sa.Column('verified_by_id', sa.Integer(), nullable=True))
    op.add_column('enrollment_proof', sa.Column('verified_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('enrollment_proof', sa.Column('needs_human_review', sa.Boolean(), nullable=False, server_default='false'))

    # Make field_of_study nullable (was nullable=False as enrollment_name)
    op.alter_column('enrollment_proof', 'field_of_study', nullable=True)

    # Drop redundant tenant columns
    op.drop_column('tenant', 'study_subject')
    op.drop_column('tenant', 'apprenticeship_field')
    op.drop_column('tenant', 'educational_institution')


def downgrade() -> None:
    op.add_column('tenant', sa.Column('educational_institution', sa.String(), nullable=True))
    op.add_column('tenant', sa.Column('apprenticeship_field', sa.String(), nullable=True))
    op.add_column('tenant', sa.Column('study_subject', sa.String(), nullable=True))

    op.drop_column('enrollment_proof', 'needs_human_review')
    op.drop_column('enrollment_proof', 'verified_at')
    op.drop_column('enrollment_proof', 'verified_by_id')
    op.drop_column('enrollment_proof', 'last_edited_by_id')
    op.drop_column('enrollment_proof', 'last_edited_at')
    op.drop_column('enrollment_proof', 'uploaded_by_id')
    op.drop_column('enrollment_proof', 'educational_institution')

    # Make field_of_study non-nullable before renaming back
    op.execute("UPDATE enrollment_proof SET field_of_study = '' WHERE field_of_study IS NULL")
    op.alter_column('enrollment_proof', 'field_of_study', nullable=False)

    op.alter_column('enrollment_proof', 'uploaded_at', new_column_name='submitted_at')
    op.alter_column('enrollment_proof', 'field_of_study', new_column_name='enrollment_name')
    # Note: Postgres does not support removing enum values; downgrade leaves SCHUELER/FSJ in the type
