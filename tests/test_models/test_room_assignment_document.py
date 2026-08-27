import uuid
from datetime import date, datetime, timezone
from decimal import Decimal

import pytest
from sqlalchemy.exc import DBAPIError

from cartei_db.models.building import Building
from cartei_db.models.wg import WG
from cartei_db.models.room import Room
from cartei_db.models.tenant import Tenant
from cartei_db.models.tenant_room_assignment import TenantRoomAssignment
from cartei_db.models.mietvertrag_document import MietvertragDocument
from cartei_db.models.mietbedingungen_document import MietbedingungenDocument
from cartei_db.models.wohnungsgeberbescheinigung_document import (
    WohnungsgeberbescheinigungDocument,
)


@pytest.fixture
def assignment(session):
    t = Tenant(
        first_name="Ra", last_name="Doc", email="ra@example.com",
        intranet_username="radoc_rad", intranet_uuid=uuid.uuid4(),
        is_flinta=False, barrier_free_needed=False,
        mailbox_list_opt_in=False, soli_miete_wunsch=Decimal("0"),
    )
    session.add(t)
    session.flush()
    b = Building(name="NB_RAD")
    session.add(b)
    session.flush()
    w = WG(building_id=b.id, name="3.03")
    session.add(w)
    session.flush()
    r = Room(
        wg_id=w.id, name="3.03.1", size_sqm=Decimal("11.00"),
        has_mattress=False, has_bed=False, has_table=False,
        has_closet=False, freifinanziert=False,
    )
    session.add(r)
    session.flush()
    a = TenantRoomAssignment(tenant_id=t.id, room_id=r.id, moved_in=date(2024, 9, 1))
    session.add(a)
    session.flush()
    a._tenant = t
    return a


def _assignment_common(assignment):
    """Per-assignment document (Wohnungsgeberbescheinigung), keyed on the tenancy."""
    return dict(
        tenant_room_assignment_id=assignment.id,
        file_name="doc.pdf", file_data=b"%PDF-1.4 x",
        uploaded_at=datetime(2026, 8, 2, 9, 0, tzinfo=timezone.utc),
        uploaded_by_id=assignment._tenant.id,
    )


def _tenant_common(assignment):
    """Per-tenant document (Mietvertrag, Mietbedingungen), keyed on the person."""
    return dict(
        tenant_id=assignment._tenant.id,
        file_name="doc.pdf", file_data=b"%PDF-1.4 x",
        uploaded_at=datetime(2026, 8, 2, 9, 0, tzinfo=timezone.utc),
        uploaded_by_id=assignment._tenant.id,
    )


def test_store_mietvertrag(session, assignment):
    doc = MietvertragDocument(
        **_tenant_common(assignment),
        renter_signed_at=date(2026, 8, 1),
        company_signed_at=date(2026, 8, 3),
        company_signed_by_id=assignment._tenant.id,
    )
    session.add(doc)
    session.flush()
    fetched = session.get(MietvertragDocument, doc.id)
    assert fetched.renter_signed_at == date(2026, 8, 1)
    assert fetched.company_signed_at == date(2026, 8, 3)
    assert fetched.company_signed_by_id == assignment._tenant.id
    assert fetched.revoked_at is None


def test_store_mietbedingungen(session, assignment):
    doc = MietbedingungenDocument(**_tenant_common(assignment), signed_at=date(2026, 8, 1))
    session.add(doc)
    session.flush()
    assert session.get(MietbedingungenDocument, doc.id).signed_at == date(2026, 8, 1)


def test_store_wohnungsgeberbescheinigung(session, assignment):
    doc = WohnungsgeberbescheinigungDocument(
        **_assignment_common(assignment),
        signed_at=date(2026, 8, 1),
        company_signed_by_id=assignment._tenant.id,
    )
    session.add(doc)
    session.flush()
    fetched = session.get(WohnungsgeberbescheinigungDocument, doc.id)
    assert fetched.signed_at == date(2026, 8, 1)
    assert fetched.company_signed_by_id == assignment._tenant.id


def test_delete_is_rejected(session, assignment):
    doc = MietbedingungenDocument(**_tenant_common(assignment), signed_at=date(2026, 8, 1))
    session.add(doc)
    session.flush()
    session.delete(doc)
    with pytest.raises(DBAPIError):
        session.flush()


def test_non_revoke_update_is_rejected(session, assignment):
    doc = MietbedingungenDocument(**_tenant_common(assignment), signed_at=date(2026, 8, 1))
    session.add(doc)
    session.flush()
    doc.file_name = "changed.pdf"
    with pytest.raises(DBAPIError):
        session.flush()


def test_revoke_with_note_succeeds(session, assignment):
    doc = MietbedingungenDocument(**_tenant_common(assignment), signed_at=date(2026, 8, 1))
    session.add(doc)
    session.flush()
    doc.revoked_at = datetime(2026, 8, 10, tzinfo=timezone.utc)
    doc.revoked_by_id = assignment._tenant.id
    doc.revoked_note = "widerruf"
    session.flush()
    assert session.get(MietbedingungenDocument, doc.id).revoked_at is not None


def test_revoke_without_note_is_rejected(session, assignment):
    doc = MietbedingungenDocument(**_tenant_common(assignment), signed_at=date(2026, 8, 1))
    session.add(doc)
    session.flush()
    doc.revoked_at = datetime(2026, 8, 10, tzinfo=timezone.utc)
    doc.revoked_by_id = assignment._tenant.id
    doc.revoked_note = "   "
    with pytest.raises(DBAPIError):
        session.flush()
