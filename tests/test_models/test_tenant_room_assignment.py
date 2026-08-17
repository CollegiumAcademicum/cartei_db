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
        is_flinta=False, barrier_free_needed=False,
        mailbox_list_opt_in=False, soli_miete_wunsch=Decimal("0"),
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


def test_sublet_and_key_dates_on_assignment(session, tenant, room):
    primary = Tenant(
        first_name="Primary", last_name="Renter", email="prim@example.com",
        intranet_username="primary_tra", intranet_uuid=uuid.uuid4(),
        is_flinta=False, barrier_free_needed=False,
        mailbox_list_opt_in=False, soli_miete_wunsch=Decimal("0"),
    )
    session.add(primary)
    session.flush()
    a = TenantRoomAssignment(
        tenant_id=tenant.id, room_id=room.id, moved_in=date(2024, 1, 1),
        mailbox_key_received=date(2024, 1, 3), mailbox_key_returned=date(2024, 6, 29),
        is_sublet=True, sublet_of_tenant_id=primary.id,
        key_received=date(2024, 1, 2), key_returned=date(2024, 6, 30),
    )
    session.add(a)
    session.flush()
    got = session.get(TenantRoomAssignment, a.id)
    assert got.mailbox_key_received == date(2024, 1, 3)
    assert got.mailbox_key_returned == date(2024, 6, 29)
    assert got.is_sublet is True
    assert got.sublet_of_tenant_id == primary.id
    assert got.key_received == date(2024, 1, 2)
    assert got.key_returned == date(2024, 6, 30)
