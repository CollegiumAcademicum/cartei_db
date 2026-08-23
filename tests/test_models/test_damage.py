import uuid
from datetime import datetime, timezone
from decimal import Decimal

import pytest

from cartei_db.enums import RoomDamageLine, WGDamageLine, DamageSize
from cartei_db.models.building import Building
from cartei_db.models.wg import WG
from cartei_db.models.room import Room
from cartei_db.models.tenant import Tenant
from cartei_db.models.room_damage import RoomDamage
from cartei_db.models.wg_damage import WGDamage


@pytest.fixture
def fixtures(session):
    b = Building(name="Altbau")
    session.add(b)
    session.flush()
    wg = WG(building_id=b.id, name="WG 1")
    session.add(wg)
    session.flush()
    room = Room(wg_id=wg.id, name="1.01", size_sqm=Decimal("10"))
    session.add(room)
    t = Tenant(
        first_name="Da", last_name="Mage", email="d@example.com",
        intranet_username="dmage", intranet_uuid=uuid.uuid4(),
        is_flinta=False, barrier_free_needed=False,
        mailbox_list_opt_in=False, soli_miete_wunsch=Decimal("0"),
    )
    session.add(t)
    session.flush()
    return {"wg": wg, "room": room, "tenant": t}


def test_room_damage_opens_unfixed(session, fixtures):
    d = RoomDamage(
        room_id=fixtures["room"].id, line=RoomDamageLine.WAND_LOECHER,
        size=DamageSize.LT1, note="neben Fenster",
        created_at=datetime(2026, 8, 22, tzinfo=timezone.utc),
        created_by_id=fixtures["tenant"].id,
    )
    session.add(d)
    session.flush()
    fetched = session.get(RoomDamage, d.id)
    assert fetched.fixed_at is None
    assert fetched.line == RoomDamageLine.WAND_LOECHER


def test_wg_damage_persists(session, fixtures):
    d = WGDamage(
        wg_id=fixtures["wg"].id, line=WGDamageLine.BAD_FLECK,
        created_at=datetime(2026, 8, 22, tzinfo=timezone.utc),
        created_by_id=fixtures["tenant"].id,
    )
    session.add(d)
    session.flush()
    assert session.get(WGDamage, d.id).size is None


from datetime import datetime as _dt
from sqlalchemy.exc import DBAPIError


def _open_room_damage(session, fixtures):
    d = RoomDamage(
        room_id=fixtures["room"].id, line=RoomDamageLine.BODEN_FLECKEN,
        created_at=_dt(2026, 8, 22, tzinfo=timezone.utc),
        created_by_id=fixtures["tenant"].id,
    )
    session.add(d)
    session.flush()
    return d


def test_delete_is_rejected(session, fixtures):
    d = _open_room_damage(session, fixtures)
    session.delete(d)
    with pytest.raises(DBAPIError):
        session.flush()


def test_fix_and_reopen_are_allowed(session, fixtures):
    d = _open_room_damage(session, fixtures)
    d.fixed_at = _dt(2026, 8, 23, tzinfo=timezone.utc)
    d.fixed_by_id = fixtures["tenant"].id
    session.flush()
    assert session.get(RoomDamage, d.id).fixed_at is not None
    # reopen
    d.fixed_at = None
    d.fixed_by_id = None
    session.flush()
    assert session.get(RoomDamage, d.id).fixed_at is None


def test_note_edit_is_allowed(session, fixtures):
    d = _open_room_damage(session, fixtures)
    d.note = "Nachtrag"
    session.flush()
    assert session.get(RoomDamage, d.id).note == "Nachtrag"
