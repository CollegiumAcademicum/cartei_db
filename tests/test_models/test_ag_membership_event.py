import uuid
from datetime import datetime, timezone
from decimal import Decimal

import pytest
from sqlalchemy.exc import DBAPIError

from cartei_db.enums import AGMembershipAction
from cartei_db.models.ag_membership_event import AGMembershipEvent
from cartei_db.models.tenant import Tenant


@pytest.fixture
def event(session):
    t = Tenant(
        first_name="Lea", last_name="Test", email="lea@example.com",
        intranet_username="ltest_ame", intranet_uuid=uuid.uuid4(),
        is_flinta=True, barrier_free_needed=False,
        mailbox_list_opt_in=False, soli_miete_wunsch=Decimal("0"),
    )
    session.add(t)
    session.flush()
    ev = AGMembershipEvent(
        tenant_id=t.id, uid="ltest_ame", group_cn="ag.garten",
        action=AGMembershipAction.JOIN, actor_username="ltest_ame",
        created_at=datetime(2026, 11, 13, 9, 0, tzinfo=timezone.utc),
    )
    session.add(ev)
    session.flush()
    return ev


def test_event_is_written(session, event):
    fetched = session.get(AGMembershipEvent, event.id)
    assert fetched.action == AGMembershipAction.JOIN
    assert fetched.group_cn == "ag.garten"


def test_update_is_rejected(session, event):
    event.action = AGMembershipAction.LEAVE
    with pytest.raises(DBAPIError):
        session.flush()


def test_delete_is_rejected(session, event):
    session.delete(event)
    with pytest.raises(DBAPIError):
        session.flush()


def test_event_without_tenant(session):
    ev = AGMembershipEvent(
        tenant_id=None, uid="ghost", group_cn="ag.garten",
        action=AGMembershipAction.LEAVE, actor_username="lea",
        created_at=datetime(2026, 11, 13, tzinfo=timezone.utc),
    )
    session.add(ev)
    session.flush()
    fetched = session.get(AGMembershipEvent, ev.id)
    assert (fetched.tenant_id, fetched.actor_username) == (None, "lea")
