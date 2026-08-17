import uuid
from datetime import date, datetime, timezone
from decimal import Decimal

import pytest
from sqlalchemy.exc import DBAPIError

from cartei_db.enums import DocumentType
from cartei_db.models.document import Document
from cartei_db.models.tenant import Tenant


@pytest.fixture
def document(session):
    t = Tenant(
        first_name="Im", last_name="Mutable", email="im@example.com",
        intranet_username="immut_doc", intranet_uuid=uuid.uuid4(),
        is_flinta=False, barrier_free_needed=False,
        mailbox_list_opt_in=False, soli_miete_wunsch=Decimal("0"),
    )
    session.add(t)
    session.flush()
    doc = Document(
        tenant_id=t.id, document_type=DocumentType.datenschutz,
        file_name="d.pdf", file_data=b"x", signed_at=date(2026, 8, 1),
        uploaded_at=datetime(2026, 8, 2, tzinfo=timezone.utc), uploaded_by_id=t.id,
    )
    session.add(doc)
    session.flush()
    return doc


def test_delete_is_rejected(session, document):
    session.delete(document)
    with pytest.raises(DBAPIError):
        session.flush()


def test_non_revoke_update_is_rejected(session, document):
    document.file_name = "changed.pdf"
    with pytest.raises(DBAPIError):
        session.flush()


def test_revoke_without_note_is_rejected(session, document):
    document.revoked_at = datetime(2026, 8, 10, tzinfo=timezone.utc)
    document.revoked_by_id = document.uploaded_by_id
    document.revoked_note = "   "  # blank
    with pytest.raises(DBAPIError):
        session.flush()


def test_revoke_with_note_succeeds(session, document):
    document.revoked_at = datetime(2026, 8, 10, tzinfo=timezone.utc)
    document.revoked_by_id = document.uploaded_by_id
    document.revoked_note = "Einwilligung widerrufen"
    session.flush()
    fetched = session.get(Document, document.id)
    assert fetched.revoked_at is not None
    assert fetched.revoked_note == "Einwilligung widerrufen"


def test_second_revocation_is_rejected(session, document):
    document.revoked_at = datetime(2026, 8, 10, tzinfo=timezone.utc)
    document.revoked_by_id = document.uploaded_by_id
    document.revoked_note = "erst"
    session.flush()
    document.revoked_note = "nochmal"
    with pytest.raises(DBAPIError):
        session.flush()


def test_revoke_may_not_change_other_columns(session, document):
    document.revoked_at = datetime(2026, 8, 10, tzinfo=timezone.utc)
    document.revoked_by_id = document.uploaded_by_id
    document.revoked_note = "widerruf"
    document.file_name = "sneaky.pdf"
    with pytest.raises(DBAPIError):
        session.flush()
