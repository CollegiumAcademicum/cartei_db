import uuid
from datetime import date
from decimal import Decimal
import pytest
from cartei_db.models.building import Building
from cartei_db.models.wg import WG
from cartei_db.models.room import Room
from cartei_db.models.tenant import Tenant
from cartei_db.models.tenant_room_assignment import TenantRoomAssignment


@pytest.fixture
def tenant(session):
    t = Tenant(
        first_name="Max", last_name="Muster", email="max@example.com",
        intranet_username="mmuster_tra", intranet_uuid=uuid.uuid4(),
        is_flinta=False, barrier_free_needed=False, mailbox_key=False,
        mailbox_list_opt_in=False, soli_miete_wunsch=Decimal("0"),
        is_sublet=False, move_in=date(2023, 9, 1),
    )
    session.add(t)
    session.flush()
    return t


@pytest.fixture
def room(session):
    b = Building(name="NB_TRA")
    session.add(b)
    session.flush()
    w = WG(building_id=b.id, name="2.03")
    session.add(w)
    session.flush()
    r = Room(
        wg_id=w.id, name="2.03.1", size_sqm=Decimal("11.00"),
        has_mattress=False, has_bed=False, has_table=False,
        has_closet=False, freifinanziert=False,
    )
    session.add(r)
    session.flush()
    return r


def test_assign_tenant_to_room(session, tenant, room):
    a = TenantRoomAssignment(
        tenant_id=tenant.id, room_id=room.id, moved_in=date(2023, 9, 1)
    )
    session.add(a)
    session.flush()
    assert a.id is not None
    assert a.moved_out is None


def test_current_assignment_query(session, tenant, room):
    session.add(TenantRoomAssignment(
        tenant_id=tenant.id, room_id=room.id, moved_in=date(2023, 9, 1)
    ))
    session.flush()
    current = session.query(TenantRoomAssignment).filter(
        TenantRoomAssignment.tenant_id == tenant.id,
        TenantRoomAssignment.moved_out.is_(None),
    ).one()
    assert current.room_id == room.id


def test_move_out(session, tenant, room):
    a = TenantRoomAssignment(
        tenant_id=tenant.id, room_id=room.id, moved_in=date(2023, 9, 1)
    )
    session.add(a)
    session.flush()
    a.moved_out = date(2024, 3, 31)
    session.flush()
    assert session.get(TenantRoomAssignment, a.id).moved_out == date(2024, 3, 31)
