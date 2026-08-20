import uuid
from datetime import date, datetime, timezone

from cartei_db.enums import (
    DamageLine, FurnitureSource, MattressSource, PartitionPosition, UebergabeProtokollType,
)
from cartei_db.models import (
    Building, Room, Tenant, TenantRoomAssignment, UebergabeProtokoll, UebergabeProtokollDamage, WG,
)


def test_enums_have_expected_members():
    assert {e.value for e in UebergabeProtokollType} == {"EINZUG", "AUSZUG"}
    assert {e.value for e in PartitionPosition} == {"SQM_7", "SQM_14"}
    assert {e.value for e in FurnitureSource} == {"GEFRAEST", "MOEBELSPENDE", "NICHT_VORHANDEN"}
    assert {e.value for e in MattressSource} == {"CA", "NICHT_VORHANDEN"}
    assert len(DamageLine) == 18
    assert DamageLine.FENSTER_RAHMEN_FLECKEN.value == "FENSTER_RAHMEN_FLECKEN"


def _assignment(session):
    b = Building(name="Neubau"); session.add(b); session.flush()
    wg = WG(building_id=b.id, name="NB 1"); session.add(wg); session.flush()
    room = Room(wg_id=wg.id, name="1.01", size_sqm=14); session.add(room); session.flush()
    t = Tenant(first_name="A", last_name="B", email="a@example.com", intranet_username="ab", intranet_uuid=uuid.uuid4()); session.add(t); session.flush()
    a = TenantRoomAssignment(tenant_id=t.id, room_id=room.id, moved_in=date(2026, 1, 1))
    session.add(a); session.flush()
    return a, t


def test_protocol_and_damage_round_trip(session):
    a, t = _assignment(session)
    p = UebergabeProtokoll(
        tenant_room_assignment_id=a.id, protocol_type=UebergabeProtokollType.EINZUG,
        created_at=datetime.now(timezone.utc),
    )
    session.add(p); session.flush()
    d = UebergabeProtokollDamage(protocol_id=p.id, line=DamageLine.BODEN_FLECKEN, count_lt1=2, note="Ecke")
    session.add(d); session.flush()
    assert d.count_mid == 0 and d.count_gt == 0
    assert session.get(UebergabeProtokoll, p.id).damages[0].line == DamageLine.BODEN_FLECKEN


import pytest
from sqlalchemy.exc import DBAPIError

from cartei_db.models import UebergabeProtokollDocument


def test_scan_is_append_only(session):
    a, t = _assignment(session)
    p = UebergabeProtokoll(tenant_room_assignment_id=a.id,
                           protocol_type=UebergabeProtokollType.AUSZUG,
                           created_at=datetime.now(timezone.utc))
    session.add(p); session.flush()
    doc = UebergabeProtokollDocument(
        tenant_room_assignment_id=a.id, uebergabeprotokoll_id=p.id,
        file_name="scan.pdf", file_data=b"%PDF-1.4",
        uploaded_at=datetime.now(timezone.utc), uploaded_by_id=t.id,
    )
    session.add(doc); session.flush()
    doc.revoked_at = datetime.now(timezone.utc); doc.revoked_by_id = t.id
    doc.revoked_note = "falsch"
    session.flush()  # single revocation allowed
    with pytest.raises(DBAPIError):
        doc.file_name = "other.pdf"; session.flush()
