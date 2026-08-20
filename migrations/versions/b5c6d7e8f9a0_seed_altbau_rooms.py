"""seed altbau rooms + merge SWB WGs

Revision ID: b5c6d7e8f9a0
Revises: a4b5c6d7e8f9
Create Date: 2026-08-20

Seeds the Altbau rooms (placeholder size_sqm = 0, furniture flags false) and
merges the six single-room "SWB N" WGs into one "SWB" WG whose rooms are named
"SWB 1".."SWB 6". OJ rooms use a single running number across the WGs (OJ 1's
room 9 is split into 9A/9B); FWB rooms are WG-prefixed.
"""
from decimal import Decimal
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "b5c6d7e8f9a0"
down_revision: Union[str, Sequence[str], None] = "a4b5c6d7e8f9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# WG name -> room names (order preserved).
_ROOMS = {
    "OJ 1": ["1", "2", "3", "4", "5", "6", "7", "8", "9A", "9B", "10"],
    "OJ 2": ["11", "12", "13", "14", "15"],
    "OJ 3": ["16", "17", "18", "19", "20"],
    "OJ 4": ["21", "22", "23", "24", "25", "26", "27", "28"],
    "SWB": ["SWB 1", "SWB 2", "SWB 3", "SWB 4", "SWB 5", "SWB 6"],
    "FWB 1": ["FWB 1.1", "FWB 1.2"],
    "FWB 2": ["FWB 2.1", "FWB 2.2", "FWB 2.3", "FWB 2.4", "FWB 2.5", "FWB 2.6"],
}
_SWB_DROP = ["SWB 2", "SWB 3", "SWB 4", "SWB 5", "SWB 6"]

_wg = sa.table("wg", sa.column("id"), sa.column("building_id"),
               sa.column("name"), sa.column("cluster"))
_building = sa.table("building", sa.column("id"), sa.column("name"))
_room = sa.table(
    "room", sa.column("id"), sa.column("wg_id"), sa.column("name"),
    sa.column("size_sqm"), sa.column("has_mattress"), sa.column("has_bed"),
    sa.column("has_table"), sa.column("has_closet"), sa.column("freifinanziert"),
)


def upgrade() -> None:
    conn = op.get_bind()

    # Merge SWB 1..6 -> one "SWB" WG (Altbau has no rooms/assignments yet).
    conn.execute(_wg.update().where(_wg.c.name == "SWB 1").values(name="SWB"))
    conn.execute(_wg.delete().where(_wg.c.name.in_(_SWB_DROP)))

    wg_ids = dict(conn.execute(
        sa.select(_wg.c.name, _wg.c.id).where(_wg.c.name.in_(list(_ROOMS)))
    ).all())
    rows = [
        {"wg_id": wg_ids[wg], "name": name, "size_sqm": Decimal("0.00"),
         "has_mattress": False, "has_bed": False, "has_table": False,
         "has_closet": False, "freifinanziert": False}
        for wg, names in _ROOMS.items() for name in names
    ]
    assert len(rows) == 43, len(rows)
    conn.execute(_room.insert(), rows)


def downgrade() -> None:
    conn = op.get_bind()

    wg_ids = [r[0] for r in conn.execute(
        sa.select(_wg.c.id).where(_wg.c.name.in_(list(_ROOMS)))
    ).all()]
    if wg_ids:
        conn.execute(_room.delete().where(_room.c.wg_id.in_(wg_ids)))

    # Un-merge SWB: "SWB" -> "SWB 1", re-create "SWB 2".."SWB 6".
    conn.execute(_wg.update().where(_wg.c.name == "SWB").values(name="SWB 1"))
    altbau = conn.execute(
        sa.select(_building.c.id).where(_building.c.name == "Altbau")
    ).scalar_one_or_none()
    if altbau is not None:
        conn.execute(_wg.insert(), [
            {"building_id": altbau, "name": n, "cluster": None} for n in _SWB_DROP
        ])
