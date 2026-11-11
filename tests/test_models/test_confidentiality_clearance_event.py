import uuid
from datetime import date, datetime, timezone
from decimal import Decimal

import pytest
from sqlalchemy.exc import DBAPIError

from cartei_db.enums import ConfidentialityClearanceAction
from cartei_db.models.confidentiality_clearance_event import ConfidentialityClearanceEvent
from cartei_db.models.tenant import Tenant
from cartei_db.models.vertraulichkeitserklaerung_document import (
    VertraulichkeitserklaerungDocument,
)


@pytest.fixture
def event(session):
    t = Tenant(
        first_name="Lea", last_name="Test", email="lea@example.com",
        intranet_username="ltest_cce", intranet_uuid=uuid.uuid4(),
        is_flinta=True, barrier_free_needed=False,
        mailbox_list_opt_in=False, soli_miete_wunsch=Decimal("0"),
    )
    session.add(t)
    session.flush()
    doc = VertraulichkeitserklaerungDocument(
        tenant_id=t.id, file_name="ve.pdf", file_data=b"%PDF-1.4 fake",
        signed_at=date(2026, 8, 1),
        uploaded_at=datetime(2026, 8, 2, 9, 0, tzinfo=timezone.utc),
        uploaded_by_id=t.id,
    )
    session.add(doc)
    session.flush()
    ev = ConfidentialityClearanceEvent(
        tenant_id=t.id, document_id=doc.id,
        action=ConfidentialityClearanceAction.GRANT, actor_id=None,
        created_at=datetime(2026, 11, 7, 9, 0, tzinfo=timezone.utc),
    )
    session.add(ev)
    session.flush()
    return ev


def test_event_is_written(session, event):
    fetched = session.get(ConfidentialityClearanceEvent, event.id)
    assert fetched.action == ConfidentialityClearanceAction.GRANT
    assert fetched.actor_id is None
    assert fetched.tenant_id == event.tenant_id
    assert fetched.document_id == event.document_id


def test_update_is_rejected(session, event):
    event.action = ConfidentialityClearanceAction.REVOKE
    with pytest.raises(DBAPIError):
        session.flush()


def test_delete_is_rejected(session, event):
    session.delete(event)
    with pytest.raises(DBAPIError):
        session.flush()
