import uuid
from datetime import date, datetime, timezone
from decimal import Decimal

import pytest

from cartei_db.enums import DocumentType
from cartei_db.models.document import Document
from cartei_db.models.tenant import Tenant


@pytest.fixture
def tenant(session):
    t = Tenant(
        first_name="Lea", last_name="Test", email="lea@example.com",
        intranet_username="ltest_doc", intranet_uuid=uuid.uuid4(),
        is_flinta=True, barrier_free_needed=False,
        mailbox_list_opt_in=False, soli_miete_wunsch=Decimal("0"),
    )
    session.add(t)
    session.flush()
    return t


def _document(tenant, **kwargs):
    defaults = dict(
        tenant_id=tenant.id,
        document_type=DocumentType.datenschutz,
        file_name="datenschutz.pdf",
        file_data=b"%PDF-1.4 fake",
        signed_at=date(2026, 8, 1),
        uploaded_at=datetime(2026, 8, 2, 9, 0, tzinfo=timezone.utc),
        uploaded_by_id=tenant.id,
    )
    return Document(**{**defaults, **kwargs})


def test_store_datenschutz_document(session, tenant):
    doc = _document(tenant)
    session.add(doc)
    session.flush()
    fetched = session.get(Document, doc.id)
    assert fetched.file_data == b"%PDF-1.4 fake"
    assert fetched.document_type is DocumentType.datenschutz
    assert fetched.signed_at == date(2026, 8, 1)
    assert fetched.uploaded_by_id == tenant.id
    assert fetched.revoked_at is None
    assert fetched.revoked_by_id is None
    assert fetched.revoked_note is None


def test_store_photoerlaubnis_document(session, tenant):
    doc = _document(tenant, document_type=DocumentType.photoerlaubnis, file_name="foto.pdf")
    session.add(doc)
    session.flush()
    assert session.get(Document, doc.id).document_type is DocumentType.photoerlaubnis
