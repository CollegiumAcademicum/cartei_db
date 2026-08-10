from decimal import Decimal
import pytest
from cartei_db.models.building import Building
from cartei_db.models.wg import WG
from cartei_db.models.room import Room
from cartei_db.base import EntityHistory


@pytest.fixture
def wg(session):
    b = Building(name="NB_Room")
    session.add(b)
    session.flush()
    w = WG(building_id=b.id, name="1.05")
    session.add(w)
    session.flush()
    return w


def test_create_room(session, wg):
    r = Room(
        wg_id=wg.id, name="1.05.3", size_sqm=Decimal("12.50"),
        has_mattress=True, has_bed=True, has_table=False,
        has_closet=True, freifinanziert=True,
    )
    session.add(r)
    session.flush()
    assert r.id is not None


def test_room_size_update_writes_history(session, wg):
    r = Room(
        wg_id=wg.id, name="1.05.1", size_sqm=Decimal("10.00"),
        has_mattress=False, has_bed=False, has_table=False,
        has_closet=False, freifinanziert=False,
    )
    session.add(r)
    session.flush()

    r.size_sqm = Decimal("11.50")
    session.flush()

    history = session.query(EntityHistory).filter_by(
        entity_type="room", entity_id=r.id
    ).one()
    assert history.snapshot["size_sqm"] == 10.0


def test_freifinanziert_default_false(session, wg):
    r = Room(
        wg_id=wg.id, name="1.05.2", size_sqm=Decimal("9.00"),
        has_mattress=False, has_bed=False, has_table=False,
        has_closet=False, freifinanziert=False,
    )
    session.add(r)
    session.flush()
    assert session.get(Room, r.id).freifinanziert is False
