import uuid
from datetime import date, datetime, timezone
from decimal import Decimal
import pytest
from cartei_db.models.enrollment_proof import EnrollmentProof
from cartei_db.models.tenant import Tenant
from cartei_db.enums import EnrollmentType


@pytest.fixture
def tenant(session):
    t = Tenant(
        first_name="Lea", last_name="Test", email="lea@example.com",
        intranet_username="ltest_ep", intranet_uuid=uuid.uuid4(),
        is_flinta=True, barrier_free_needed=False, mailbox_key=False,
        mailbox_list_opt_in=False, soli_miete_wunsch=Decimal("0"),
        is_sublet=False, move_in=date(2023, 9, 1),
    )
    session.add(t)
    session.flush()
    return t


def _proof(tenant, **kwargs):
    defaults = dict(
        tenant_id=tenant.id,
        enrollment_type=EnrollmentType.STUDY,
        file_data=b"%PDF-1.4 fake",
        file_name="proof.pdf",
        uploaded_at=datetime(2024, 3, 1, 10, 0, tzinfo=timezone.utc),
        valid_until=date(2024, 9, 1),
    )
    return EnrollmentProof(**{**defaults, **kwargs})


def test_store_study_proof(session, tenant):
    proof = _proof(tenant, field_of_study="Informatik B.Sc.", educational_institution="Uni Heidelberg")
    session.add(proof)
    session.flush()
    fetched = session.get(EnrollmentProof, proof.id)
    assert fetched.file_data == b"%PDF-1.4 fake"
    assert fetched.field_of_study == "Informatik B.Sc."
    assert fetched.educational_institution == "Uni Heidelberg"
    assert fetched.needs_human_review is False
    assert fetched.verified_at is None


def test_schueler_and_fsj_types(session, tenant):
    for etype in (EnrollmentType.SCHUELER, EnrollmentType.FSJ):
        p = _proof(tenant, enrollment_type=etype)
        session.add(p)
    session.flush()
    types = {p.enrollment_type for p in session.query(EnrollmentProof).filter_by(tenant_id=tenant.id).all()}
    assert EnrollmentType.SCHUELER in types
    assert EnrollmentType.FSJ in types


def test_verification(session, tenant):
    proof = _proof(tenant)
    session.add(proof)
    session.flush()
    assert proof.verified_at is None
    proof.verified_at = datetime(2024, 4, 1, tzinfo=timezone.utc)
    proof.verified_by_id = tenant.id
    session.flush()
    fetched = session.get(EnrollmentProof, proof.id)
    assert fetched.verified_at is not None
    assert fetched.verified_by_id == tenant.id


def test_needs_human_review_flag(session, tenant):
    proof = _proof(tenant, needs_human_review=True)
    session.add(proof)
    session.flush()
    assert session.get(EnrollmentProof, proof.id).needs_human_review is True


def test_review_reason_defaults_none_and_persists(session, tenant):
    p = _proof(tenant)
    session.add(p); session.flush()
    assert p.review_reason is None
    p.review_reason = "Signatur ungültig"
    session.flush(); session.refresh(p)
    assert p.review_reason == "Signatur ungültig"


def test_latest_proof_query(session, tenant):
    for month in [3, 9]:
        session.add(_proof(
            tenant,
            file_name=f"proof_{month}.pdf",
            uploaded_at=datetime(2024, month, 1, tzinfo=timezone.utc),
            valid_until=date(2024, 9, 1) if month == 3 else date(2025, 3, 1),
        ))
    session.flush()
    latest = (
        session.query(EnrollmentProof)
        .filter_by(tenant_id=tenant.id)
        .order_by(EnrollmentProof.uploaded_at.desc())
        .first()
    )
    assert latest.uploaded_at.month == 9
