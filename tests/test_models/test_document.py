import uuid
from datetime import date, datetime, timezone
from decimal import Decimal

import pytest

from cartei_db.models.datenschutz_document import DatenschutzDocument
from cartei_db.models.photoerlaubnis_document import PhotoerlaubnisDocument
from cartei_db.models.selbstverpflichtung_engagement_document import (
    SelbstverpflichtungEngagementDocument,
)
from cartei_db.models.sepa_lastschriftmandat_document import SepaLastschriftmandatDocument
from cartei_db.models.bescheid_ausbildungsstelle_document import (
    BescheidAusbildungsstelleDocument,
)
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


@pytest.mark.parametrize(
    "model",
    [DatenschutzDocument, PhotoerlaubnisDocument, SelbstverpflichtungEngagementDocument],
)
def test_store_document(session, tenant, model):
    doc = model(
        tenant_id=tenant.id,
        file_name="doc.pdf",
        file_data=b"%PDF-1.4 fake",
        signed_at=date(2026, 8, 1),
        uploaded_at=datetime(2026, 8, 2, 9, 0, tzinfo=timezone.utc),
        uploaded_by_id=tenant.id,
    )
    session.add(doc)
    session.flush()
    fetched = session.get(model, doc.id)
    assert fetched.file_data == b"%PDF-1.4 fake"
    assert fetched.signed_at == date(2026, 8, 1)
    assert fetched.uploaded_by_id == tenant.id
    assert fetched.revoked_at is None
    assert fetched.revoked_by_id is None
    assert fetched.revoked_note is None


def test_per_type_tables_are_independent(session, tenant):
    ds = DatenschutzDocument(
        tenant_id=tenant.id, file_name="ds.pdf", file_data=b"a",
        signed_at=date(2026, 8, 1),
        uploaded_at=datetime(2026, 8, 2, tzinfo=timezone.utc), uploaded_by_id=tenant.id,
    )
    pe = PhotoerlaubnisDocument(
        tenant_id=tenant.id, file_name="pe.pdf", file_data=b"b",
        signed_at=date(2026, 8, 1),
        uploaded_at=datetime(2026, 8, 2, tzinfo=timezone.utc), uploaded_by_id=tenant.id,
    )
    session.add_all([ds, pe])
    session.flush()
    assert ds.__tablename__ == "datenschutz_document"
    assert pe.__tablename__ == "photoerlaubnis_document"


def test_sepa_stores_structured_mandate_fields(session, tenant):
    doc = SepaLastschriftmandatDocument(
        tenant_id=tenant.id, file_name="sepa.pdf", file_data=b"%PDF",
        signed_at=date(2026, 8, 1),
        uploaded_at=datetime(2026, 8, 2, tzinfo=timezone.utc), uploaded_by_id=tenant.id,
        mandatsreferenz="CA-2026-0001", kontoinhaber="Lea Test",
        bank_name="Sparkasse Heidelberg", iban="DE89370400440532013000", bic="COBADEFFXXX",
    )
    session.add(doc)
    session.flush()
    fetched = session.get(SepaLastschriftmandatDocument, doc.id)
    assert fetched.mandatsreferenz == "CA-2026-0001"
    assert fetched.iban == "DE89370400440532013000"
    assert fetched.bic == "COBADEFFXXX"


def test_bescheid_records_ca_side_signer(session, tenant):
    doc = BescheidAusbildungsstelleDocument(
        tenant_id=tenant.id, file_name="bescheid.pdf", file_data=b"%PDF",
        signed_at=date(2026, 8, 1),
        uploaded_at=datetime(2026, 8, 2, tzinfo=timezone.utc), uploaded_by_id=tenant.id,
        signed_by_id=tenant.id,
    )
    session.add(doc)
    session.flush()
    assert session.get(BescheidAusbildungsstelleDocument, doc.id).signed_by_id == tenant.id
