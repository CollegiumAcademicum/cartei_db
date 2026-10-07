import uuid
from datetime import date, datetime, timezone
from decimal import Decimal

import pytest

from cartei_db.base import EntityHistory
from cartei_db.models.building import Building
from cartei_db.models.wg import WG
from cartei_db.models.room import Room
from cartei_db.models.tenant import Tenant
from cartei_db.models.uebergabe import Uebergabe


@pytest.fixture
def room(session):
    b = Building(name="NB_UB")
    session.add(b); session.flush()
    w = WG(building_id=b.id, name="3.01")
    session.add(w); session.flush()
    r = Room(wg_id=w.id, name="3.01.1", size_sqm=Decimal("11.00"),
             has_mattress=False, has_bed=False, has_table=False,
             has_closet=False, freifinanziert=False)
    session.add(r); session.flush()
    return r


@pytest.fixture
def inspector(session):
    t = Tenant(first_name="Insp", last_name="Ektor", email="insp@example.com",
               intranet_username="insp_ub", intranet_uuid=uuid.uuid4(),
               is_flinta=False, barrier_free_needed=False,
               mailbox_list_opt_in=False, soli_miete_wunsch=Decimal("0"))
    session.add(t); session.flush()
    return t


def test_create_uebergabe(session, room, inspector):
    u = Uebergabe(room_id=room.id, outgoing_assignment_id=None,
                  conducted_by_id=inspector.id,
                  conducted_at=datetime(2026, 10, 7, 12, 0, tzinfo=timezone.utc))
    session.add(u); session.flush()
    assert u.id is not None and u.completed_at is None


def test_complete_writes_history(session, room, inspector):
    u = Uebergabe(room_id=room.id, conducted_by_id=inspector.id,
                  conducted_at=datetime(2026, 10, 7, 12, 0, tzinfo=timezone.utc))
    session.add(u); session.flush()
    u.completed_at = datetime(2026, 10, 7, 13, 0, tzinfo=timezone.utc)
    session.flush()
    history = session.query(EntityHistory).filter_by(
        entity_type="uebergabe", entity_id=u.id).one()
    assert history.snapshot["completed_at"] is None


def test_create_links_outgoing_and_incoming_assignments(session, room, inspector):
    from cartei_db.models.tenant_room_assignment import TenantRoomAssignment
    out_a = TenantRoomAssignment(tenant_id=inspector.id, room_id=room.id,
                                 moved_in=date(2025, 1, 1), moved_out=date(2026, 6, 30),
                                 is_sublet=False)
    in_a = TenantRoomAssignment(tenant_id=inspector.id, room_id=room.id,
                                moved_in=date(2026, 7, 1), is_sublet=False)
    session.add_all([out_a, in_a]); session.flush()
    u = Uebergabe(room_id=room.id, conducted_by_id=inspector.id,
                  conducted_at=datetime(2026, 7, 1, 12, 0, tzinfo=timezone.utc),
                  outgoing_assignment_id=out_a.id, incoming_assignment_id=in_a.id)
    session.add(u); session.flush()
    assert u.outgoing_assignment_id == out_a.id
    assert u.incoming_assignment_id == in_a.id
