"""drop uebergabeprotokoll

Removes the Übergabeprotokoll feature (protocol, damage, document tables and
their enums) so it can be remodelled from scratch. This is the reverse of
revision 4116deb90667; downgrade re-creates the original schema.

Revision ID: c5d6e7f8a9b0
Revises: 4116deb90667
Create Date: 2026-08-21 15:10:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

from cartei_db.base import create_audit_trigger_sql, drop_audit_trigger_sql
from cartei_db.document_triggers import document_append_only_sql


# revision identifiers, used by Alembic.
revision: str = 'c5d6e7f8a9b0'
down_revision: Union[str, Sequence[str], None] = '4116deb90667'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Drop the Übergabeprotokoll tables, triggers and enums."""
    # Drop only this table's trigger; the shared document_append_only() function
    # stays because other document tables still depend on it.
    op.execute("DROP TRIGGER IF EXISTS uebergabeprotokoll_document_append_only ON uebergabeprotokoll_document")
    op.execute(drop_audit_trigger_sql('uebergabeprotokoll'))
    op.drop_table('uebergabeprotokoll_document')
    op.drop_table('uebergabeprotokoll_damage')
    op.drop_table('uebergabeprotokoll')
    sa.Enum(name='damageline').drop(op.get_bind())
    sa.Enum(name='mattresssource').drop(op.get_bind())
    sa.Enum(name='furnituresource').drop(op.get_bind())
    sa.Enum(name='partitionposition').drop(op.get_bind())
    sa.Enum(name='uebergabeprotokolltype').drop(op.get_bind())


def downgrade() -> None:
    """Re-create the original Übergabeprotokoll schema."""
    op.create_table('uebergabeprotokoll',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('tenant_room_assignment_id', sa.Integer(), nullable=False),
    sa.Column('protocol_type', sa.Enum('EINZUG', 'AUSZUG', name='uebergabeprotokolltype'), nullable=False),
    sa.Column('mv_representative_id', sa.Integer(), nullable=True),
    sa.Column('protocol_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('partition_position', sa.Enum('SQM_7', 'SQM_14', name='partitionposition'), nullable=True),
    sa.Column('barrierefrei', sa.Boolean(), nullable=False),
    sa.Column('bed_source', sa.Enum('GEFRAEST', 'MOEBELSPENDE', 'NICHT_VORHANDEN', name='furnituresource'), nullable=True),
    sa.Column('mattress_source', sa.Enum('CA', 'NICHT_VORHANDEN', name='mattresssource'), nullable=True),
    sa.Column('desk_source', sa.Enum('GEFRAEST', 'MOEBELSPENDE', 'NICHT_VORHANDEN', name='furnituresource'), nullable=True),
    sa.Column('closet_source', sa.Enum('GEFRAEST', 'MOEBELSPENDE', 'NICHT_VORHANDEN', name='furnituresource'), nullable=True),
    sa.Column('sonstige_schaeden', sa.Text(), nullable=True),
    sa.Column('sonstige_moebel', sa.Text(), nullable=True),
    sa.Column('kueche_schaeden', sa.Text(), nullable=True),
    sa.Column('bad_schaeden', sa.Text(), nullable=True),
    sa.Column('gemeinschaftsflaeche', sa.Text(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('finalized_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['mv_representative_id'], ['tenant.id'], ),
    sa.ForeignKeyConstraint(['tenant_room_assignment_id'], ['tenant_room_assignment.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.execute(create_audit_trigger_sql('uebergabeprotokoll', set()))
    op.create_table('uebergabeprotokoll_damage',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('protocol_id', sa.Integer(), nullable=False),
    sa.Column('line', sa.Enum('BODEN_FLECKEN', 'BODEN_LOECHER', 'FUSSLEISTE_FLECKEN', 'WAND_FLECKEN', 'WAND_LOECHER', 'WAND_KLEBER', 'TUER_FLECKEN', 'TUER_LOECHER', 'FENSTER_RAHMEN_FLECKEN', 'FENSTER_BANK_FLECKEN', 'FENSTER_KLEBER', 'BETT_FLECKEN', 'BETT_LOECHER', 'MATRATZE_FLECKEN', 'SCHREIBTISCH_FLECKEN', 'SCHREIBTISCH_LOECHER', 'SCHRANK_FLECKEN', 'SCHRANK_LOECHER', name='damageline'), nullable=False),
    sa.Column('count_lt1', sa.Integer(), nullable=False),
    sa.Column('count_mid', sa.Integer(), nullable=False),
    sa.Column('count_gt', sa.Integer(), nullable=False),
    sa.Column('note', sa.Text(), nullable=True),
    sa.ForeignKeyConstraint(['protocol_id'], ['uebergabeprotokoll.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('protocol_id', 'line', name='uq_uebergabeprotokoll_damage')
    )
    op.create_table('uebergabeprotokoll_document',
    sa.Column('uebergabeprotokoll_id', sa.Integer(), nullable=True),
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('tenant_room_assignment_id', sa.Integer(), nullable=False),
    sa.Column('file_name', sa.String(), nullable=False),
    sa.Column('file_data', sa.LargeBinary(), nullable=False),
    sa.Column('uploaded_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('uploaded_by_id', sa.Integer(), nullable=False),
    sa.Column('revoked_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('revoked_by_id', sa.Integer(), nullable=True),
    sa.Column('revoked_note', sa.Text(), nullable=True),
    sa.ForeignKeyConstraint(['revoked_by_id'], ['tenant.id'], ),
    sa.ForeignKeyConstraint(['tenant_room_assignment_id'], ['tenant_room_assignment.id'], ),
    sa.ForeignKeyConstraint(['uebergabeprotokoll_id'], ['uebergabeprotokoll.id'], ),
    sa.ForeignKeyConstraint(['uploaded_by_id'], ['tenant.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    for stmt in document_append_only_sql(("uebergabeprotokoll_document",)):
        op.execute(stmt)
