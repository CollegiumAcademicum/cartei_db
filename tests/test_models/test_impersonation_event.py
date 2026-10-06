from datetime import datetime, timezone

import pytest
from sqlalchemy.exc import DBAPIError

from cartei_db.enums import ImpersonationAction
from cartei_db.models.impersonation_event import ImpersonationEvent


def _event(action=ImpersonationAction.START):
    return ImpersonationEvent(
        impersonator_username="admin",
        target_username="resident",
        action=action,
        created_at=datetime(2026, 10, 6, 9, 0, tzinfo=timezone.utc),
    )


def test_event_is_written(session):
    ev = _event()
    session.add(ev)
    session.flush()
    fetched = session.get(ImpersonationEvent, ev.id)
    assert fetched.impersonator_username == "admin"
    assert fetched.target_username == "resident"
    assert fetched.action == ImpersonationAction.START


def test_update_is_rejected(session):
    ev = _event()
    session.add(ev)
    session.flush()
    ev.target_username = "someone_else"
    with pytest.raises(DBAPIError):
        session.flush()


def test_delete_is_rejected(session):
    ev = _event()
    session.add(ev)
    session.flush()
    session.delete(ev)
    with pytest.raises(DBAPIError):
        session.flush()
