"""remove room x.04.4 and compact room ids

Revision ID: f3a04b4c5d6e
Revises: 7ae6942f6d70
Create Date: 2026-08-20

Removes the 4th room of every Neubau ``.04`` WG (rooms named ``0.04.4`` ..
``3.04.4``) and any assignments to them, then renumbers ``room.id`` to be
gapless 1..N and remaps the ``tenant_room_assignment.room_id`` FKs to match.
The ``room.id`` sequence is reset so the next insert follows the last id.

The renumber temporarily drops the FK and disables the ``room`` audit trigger
so the id shuffle does not spam ``entity_history`` (the DELETEs above are still
audited). downgrade only re-creates the removed rooms (appended, new ids); the
contiguous renumber is not reversed.
"""
from typing import Sequence, Union

from alembic import op

revision: str = "f3a04b4c5d6e"
down_revision: Union[str, Sequence[str], None] = "7ae6942f6d70"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_TARGETS = "('0.04.4', '1.04.4', '2.04.4', '3.04.4')"
_TARGET_WGS = "('0.04', '1.04', '2.04', '3.04')"
_FK = "tenant_room_assignment_room_id_fkey"
_OFFSET = 1_000_000  # > room count; parks ids out of the way to avoid PK/collision during renumber


def upgrade() -> None:
    # 1. Drop the rooms (audited) and any assignments to them.
    op.execute(
        f"DELETE FROM tenant_room_assignment "
        f"WHERE room_id IN (SELECT id FROM room WHERE name IN {_TARGETS})"
    )
    op.execute(f"DELETE FROM room WHERE name IN {_TARGETS}")

    # 2. Renumber room.id -> contiguous 1..N, remapping assignment FKs.
    op.execute("ALTER TABLE room DISABLE TRIGGER room_audit")
    op.execute(f"ALTER TABLE tenant_room_assignment DROP CONSTRAINT IF EXISTS {_FK}")
    op.execute(
        "CREATE TEMP TABLE room_id_map ON COMMIT DROP AS "
        "SELECT id AS old_id, (ROW_NUMBER() OVER (ORDER BY id))::int AS new_id FROM room"
    )
    op.execute(f"UPDATE room SET id = id + {_OFFSET}")
    op.execute(f"UPDATE tenant_room_assignment SET room_id = room_id + {_OFFSET}")
    op.execute(
        f"UPDATE room r SET id = m.new_id FROM room_id_map m WHERE r.id = m.old_id + {_OFFSET}"
    )
    op.execute(
        f"UPDATE tenant_room_assignment a SET room_id = m.new_id "
        f"FROM room_id_map m WHERE a.room_id = m.old_id + {_OFFSET}"
    )
    op.execute("ALTER TABLE room ENABLE TRIGGER room_audit")
    op.create_foreign_key(_FK, "tenant_room_assignment", "room", ["room_id"], ["id"])
    op.execute(
        "SELECT setval(pg_get_serial_sequence('room', 'id'), (SELECT max(id) FROM room))"
    )


def downgrade() -> None:
    # Best-effort: re-create the removed rooms (placeholder seed values), appended
    # with fresh ids. The contiguous renumber above is not reversed.
    op.execute(
        "INSERT INTO room (wg_id, name, size_sqm, has_mattress, has_bed, "
        "has_table, has_closet, freifinanziert) "
        "SELECT w.id, w.name || '.4', 0.00, false, false, false, false, false "
        "FROM wg w JOIN building b ON b.id = w.building_id "
        f"WHERE b.name = 'Neubau' AND w.name IN {_TARGET_WGS}"
    )
    op.execute(
        "SELECT setval(pg_get_serial_sequence('room', 'id'), (SELECT max(id) FROM room))"
    )
