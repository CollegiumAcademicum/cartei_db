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


def test_store_study_proof(session, tenant):
    proof = EnrollmentProof(
        tenant_id=tenant.id,
        enrollment_type=EnrollmentType.STUDY,
        enrollment_name="Informatik B.Sc.",
        file_data=b"%PDF-1.4 fake content",
        file_name="immatrikulation.pdf",
        submitted_at=datetime(2024, 3, 1, 10, 0, tzinfo=timezone.utc),
        valid_until=date(2024, 9, 1),
    )
    session.add(proof)
    session.flush()
    fetched = session.get(EnrollmentProof, proof.id)
    assert fetched.file_data == b"%PDF-1.4 fake content"
    assert fetched.enrollment_name == "Informatik B.Sc."


def test_latest_proof_query(session, tenant):
    for month in [3, 9]:
        session.add(EnrollmentProof(
            tenant_id=tenant.id,
            enrollment_type=EnrollmentType.STUDY,
            enrollment_name="Informatik B.Sc.",
            file_data=b"pdf",
            file_name=f"proof_{month}.pdf",
            submitted_at=datetime(2024, month, 1, tzinfo=timezone.utc),
            valid_until=date(2024, 9, 1) if month == 3 else date(2025, 3, 1),
        ))
    session.flush()
    latest = (
        session.query(EnrollmentProof)
        .filter_by(tenant_id=tenant.id)
        .order_by(EnrollmentProof.submitted_at.desc())
        .first()
    )
    assert latest.submitted_at.month == 9


def test_apprenticeship_proof(session, tenant):
    proof = EnrollmentProof(
        tenant_id=tenant.id,
        enrollment_type=EnrollmentType.APPRENTICESHIP,
        enrollment_name="Tischler",
        file_data=b"contract bytes",
        file_name="ausbildungsvertrag.pdf",
        submitted_at=datetime(2024, 3, 1, tzinfo=timezone.utc),
        valid_until=date(2024, 9, 1),
    )
    session.add(proof)
    session.flush()
    assert proof.enrollment_type == EnrollmentType.APPRENTICESHIP
