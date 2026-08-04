import pytest
from sqlalchemy.exc import IntegrityError

from cartei_db.models.building import Building
from cartei_db.models.wg import WG


def test_create_building(session):
    b = Building(name="Neubau")
    session.add(b)
    session.flush()
    assert b.id is not None
    assert session.get(Building, b.id).name == "Neubau"


def test_create_wg(session):
    b = Building(name="Altbau")
    session.add(b)
    session.flush()
    wg = WG(building_id=b.id, name="OJ1")
    session.add(wg)
    session.flush()
    assert wg.id is not None
    assert wg.name == "OJ1"


def test_wg_requires_valid_building(session):
    with pytest.raises(IntegrityError):
        with session.begin_nested():  # savepoint — keeps outer transaction usable
            wg = WG(building_id=999999, name="Ghost")
            session.add(wg)
            session.flush()
