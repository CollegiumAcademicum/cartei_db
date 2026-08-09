"""seed_buildings_wgs_rooms

Revision ID: e3f4a5b6c7d8
Revises: d2e3f4a5b6c7
Create Date: 2026-08-09

Seeds the static building layout: Altbau + Neubau, their WGs, and Neubau rooms
(placeholder size_sqm = 0, all furniture flags false). Altbau rooms are not
seeded yet.

"""
from decimal import Decimal
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "e3f4a5b6c7d8"
down_revision: Union[str, Sequence[str], None] = "d2e3f4a5b6c7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Neubau cluster per WG number yy: A=01-03, B=04-07, C=08-10, D=11-13.
_CLUSTER_BY_YY = {1: "A", 2: "A", 3: "A", 4: "B", 5: "B", 6: "B", 7: "B",
                  8: "C", 9: "C", 10: "C", 11: "D", 12: "D", 13: "D"}

_ALTBAU_WGS = ["OJ1", "OJ2", "OJ3", "OJ4",
               "SWB 1", "SWB 2", "SWB 3", "SWB 4", "SWB 5", "SWB 6",
               "FWB 1", "FWB 2"]

_building = sa.table("building", sa.column("id"), sa.column("name"))
_wg = sa.table("wg", sa.column("id"), sa.column("building_id"),
               sa.column("name"), sa.column("cluster"))
_room = sa.table(
    "room", sa.column("id"), sa.column("wg_id"), sa.column("name"),
    sa.column("size_sqm"), sa.column("has_mattress"), sa.column("has_bed"),
    sa.column("has_table"), sa.column("has_closet"), sa.column("freifinanziert"),
)


def _neubau_wgs():
    """Floor 0: .01-.07; floors 1-3: .01-.13. Name x.yy, cluster str(floor)+letter."""
    for floor in range(4):
        for yy in range(1, 8 if floor == 0 else 14):
            yield {"name": f"{floor}.{yy:02d}", "cluster": f"{floor}{_CLUSTER_BY_YY[yy]}"}


def upgrade() -> None:
    conn = op.get_bind()

    conn.execute(_building.insert(), [{"name": "Altbau"}, {"name": "Neubau"}])
    bids = dict(conn.execute(sa.select(_building.c.name, _building.c.id)).all())

    wg_rows = [{"building_id": bids["Neubau"], **w} for w in _neubau_wgs()]
    wg_rows += [{"building_id": bids["Altbau"], "name": n, "cluster": None} for n in _ALTBAU_WGS]
    assert len(wg_rows) == 46 + 12, len(wg_rows)
    conn.execute(_wg.insert(), wg_rows)

    wg_ids = dict(conn.execute(
        sa.select(_wg.c.name, _wg.c.id).where(_wg.c.building_id == bids["Neubau"])
    ).all())
    room_rows = []
    for w in _neubau_wgs():
        name = w["name"]
        count = 3 if name.endswith(".05") else 4  # .05 WGs have 3 rooms, rest 4
        for z in range(1, count + 1):
            room_rows.append({
                "wg_id": wg_ids[name], "name": f"{name}.{z}",
                "size_sqm": Decimal("0.00"),
                "has_mattress": False, "has_bed": False, "has_table": False,
                "has_closet": False, "freifinanziert": False,
            })
    assert len(room_rows) == 180, len(room_rows)
    conn.execute(_room.insert(), room_rows)


def downgrade() -> None:
    conn = op.get_bind()
    bids = [r[0] for r in conn.execute(
        sa.select(_building.c.id).where(_building.c.name.in_(["Altbau", "Neubau"]))
    ).all()]
    if not bids:
        return
    wg_ids = [r[0] for r in conn.execute(
        sa.select(_wg.c.id).where(_wg.c.building_id.in_(bids))
    ).all()]
    if wg_ids:
        conn.execute(_room.delete().where(_room.c.wg_id.in_(wg_ids)))
        conn.execute(_wg.delete().where(_wg.c.id.in_(wg_ids)))
    conn.execute(_building.delete().where(_building.c.id.in_(bids)))