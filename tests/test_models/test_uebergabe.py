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
    u = Uebergabe(room_id=room.id, tenant_room_assignment_id=None,
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


def test_create_with_incoming_tenant(session, room, inspector):
    incoming = Tenant(first_name="In", last_name="Coming", email="in@example.com",
                      intranet_username="incoming_ub", intranet_uuid=uuid.uuid4(),
                      is_flinta=False, barrier_free_needed=False,
                      mailbox_list_opt_in=False, soli_miete_wunsch=Decimal("0"))
    session.add(incoming); session.flush()
    u = Uebergabe(room_id=room.id, conducted_by_id=inspector.id,
                  conducted_at=datetime(2026, 10, 7, 12, 0, tzinfo=timezone.utc),
                  incoming_tenant_id=incoming.id)
    session.add(u); session.flush()
    assert u.incoming_tenant_id == incoming.id
