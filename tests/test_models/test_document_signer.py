import uuid
from datetime import date, datetime, timezone
from decimal import Decimal

import pytest
from sqlalchemy.exc import IntegrityError

from cartei_db.models.datenschutz_document import DatenschutzDocument
from cartei_db.models.document_signer import DocumentSigner
from cartei_db.models.tenant import Tenant


def _tenant(session, username):
    t = Tenant(
        first_name="A", last_name="B", email=f"{username}@example.com",
        intranet_username=username, intranet_uuid=uuid.uuid4(),
        is_flinta=False, barrier_free_needed=False,
        mailbox_list_opt_in=False, soli_miete_wunsch=Decimal("0"),
    )
    session.add(t)
    session.flush()
    return t


@pytest.fixture
def document(session):
    subject = _tenant(session, "subj_ds")
    doc = DatenschutzDocument(
        tenant_id=subject.id, file_name="d.pdf", file_data=b"x",
        signed_at=date(2026, 8, 1),
        uploaded_at=datetime(2026, 8, 2, tzinfo=timezone.utc), uploaded_by_id=subject.id,
    )
    session.add(doc)
    session.flush()
    return doc


def test_multiple_signers(session, document):
    a = _tenant(session, "signer_a")
    b = _tenant(session, "signer_b")
    session.add_all([
        DocumentSigner(document_type="datenschutz", document_id=document.id, tenant_id=a.id),
        DocumentSigner(document_type="datenschutz", document_id=document.id, tenant_id=b.id),
    ])
    session.flush()
    signers = session.query(DocumentSigner).filter_by(
        document_type="datenschutz", document_id=document.id,
    ).all()
    assert {s.tenant_id for s in signers} == {a.id, b.id}


def test_same_id_different_type_coexist(session, document):
    """A datenschutz doc and a photoerlaubnis doc can share an id; the signer's
    document_type keeps their signers distinct."""
    a = _tenant(session, "signer_poly")
    session.add_all([
        DocumentSigner(document_type="datenschutz", document_id=document.id, tenant_id=a.id),
        DocumentSigner(document_type="photoerlaubnis", document_id=document.id, tenant_id=a.id),
    ])
    session.flush()
    assert session.query(DocumentSigner).filter_by(document_id=document.id).count() == 2


def test_duplicate_signer_rejected(session, document):
    a = _tenant(session, "signer_dup")
    session.add(DocumentSigner(document_type="datenschutz", document_id=document.id, tenant_id=a.id))
    session.flush()
    session.add(DocumentSigner(document_type="datenschutz", document_id=document.id, tenant_id=a.id))
    with pytest.raises(IntegrityError):
        session.flush()
