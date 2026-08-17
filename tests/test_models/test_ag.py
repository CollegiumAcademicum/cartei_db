import uuid
from datetime import date, datetime, timezone
from decimal import Decimal
import pytest
from cartei_db.models.ag_abfrage import AGAbfrage
from cartei_db.models.ag_abfrage_result import AGAbfrageResult
from cartei_db.models.tenant import Tenant
from cartei_db.base import EntityHistory
from cartei_db.enums import AGStatus


@pytest.fixture
def tenant(session):
    t = Tenant(
        first_name="Test", last_name="User", email="t@example.com",
        intranet_username="tuser_ag", intranet_uuid=uuid.uuid4(),
        is_flinta=False, barrier_free_needed=False,
        mailbox_list_opt_in=False, soli_miete_wunsch=Decimal("0"),
    )
    session.add(t)
    session.flush()
    return t


@pytest.fixture
def abfrage(session):
    a = AGAbfrage(
        date=date(2024, 3, 1),
        label="Abfrage 2024-1",
        ends_at=date(2024, 3, 31),
        grace_ends_at=date(2024, 4, 7),
    )
    session.add(a)
    session.flush()
    return a


def test_create_abfrage(session, abfrage):
    assert abfrage.id is not None
    assert abfrage.ends_at == date(2024, 3, 31)
    assert abfrage.grace_ends_at == date(2024, 4, 7)


def test_create_result(session, tenant, abfrage):
    result = AGAbfrageResult(
        abfrage_id=abfrage.id, ag_name="ag.kueche",
        tenant_id=tenant.id, status=AGStatus.AKTIV,
    )
    session.add(result)
    session.flush()
    assert result.id is not None
    assert result.note is None


def test_result_with_note(session, tenant, abfrage):
    result = AGAbfrageResult(
        abfrage_id=abfrage.id, ag_name="ag.kueche",
        tenant_id=tenant.id, status=AGStatus.AKTIV,
        note="Very engaged this round",
    )
    session.add(result)
    session.flush()
    assert result.note == "Very engaged this round"


def test_multiple_ags_per_tenant_per_round(session, tenant, abfrage):
    for ag in ["ag.kueche", "ag.garten"]:
        session.add(AGAbfrageResult(
            abfrage_id=abfrage.id, ag_name=ag,
            tenant_id=tenant.id, status=AGStatus.AKTIV,
        ))
    session.flush()
    results = session.query(AGAbfrageResult).filter_by(
        abfrage_id=abfrage.id, tenant_id=tenant.id
    ).all()
    assert len(results) == 2


def test_result_status_update_writes_history(session, tenant, abfrage):
    result = AGAbfrageResult(
        abfrage_id=abfrage.id, ag_name="ag.kueche",
        tenant_id=tenant.id, status=AGStatus.AKTIV,
    )
    session.add(result)
    session.flush()
    result.status = AGStatus.NICHT_AUSREICHEND
    session.flush()
    history = session.query(EntityHistory).filter_by(
        entity_type="ag_abfrage_result", entity_id=result.id
    ).one()
    assert history.snapshot["status"] == "AKTIV"