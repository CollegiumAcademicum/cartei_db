import uuid
from datetime import date
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
        is_flinta=False, barrier_free_needed=False, mailbox_key=False,
        mailbox_list_opt_in=False, soli_miete_wunsch=Decimal("0"),
        is_sublet=False, move_in=date(2023, 9, 1),
    )
    session.add(t)
    session.flush()
    return t


def test_create_abfrage(session):
    a = AGAbfrage(date=date(2024, 3, 1), label="Abfrage 2024-1")
    session.add(a)
    session.flush()
    assert a.id is not None


def test_create_result(session, tenant):
    abfrage = AGAbfrage(date=date(2024, 3, 1))
    session.add(abfrage)
    session.flush()
    result = AGAbfrageResult(
        abfrage_id=abfrage.id, ag_name="AG Küche",
        tenant_id=tenant.id, status=AGStatus.ACTIVE,
    )
    session.add(result)
    session.flush()
    assert result.id is not None


def test_multiple_ags_per_tenant_per_round(session, tenant):
    abfrage = AGAbfrage(date=date(2024, 3, 1))
    session.add(abfrage)
    session.flush()
    for ag in ["AG Küche", "AG Garten"]:
        session.add(AGAbfrageResult(
            abfrage_id=abfrage.id, ag_name=ag,
            tenant_id=tenant.id, status=AGStatus.ACTIVE,
        ))
    session.flush()
    results = session.query(AGAbfrageResult).filter_by(
        abfrage_id=abfrage.id, tenant_id=tenant.id
    ).all()
    assert len(results) == 2


def test_result_status_update_writes_history(session, tenant):
    abfrage = AGAbfrage(date=date(2024, 6, 1))
    session.add(abfrage)
    session.flush()
    result = AGAbfrageResult(
        abfrage_id=abfrage.id, ag_name="AG Küche",
        tenant_id=tenant.id, status=AGStatus.ACTIVE,
    )
    session.add(result)
    session.flush()
    result.status = AGStatus.NOT_ACTIVE_ENOUGH
    session.flush()
    history = session.query(EntityHistory).filter_by(
        entity_type="ag_abfrage_result", entity_id=result.id
    ).one()
    assert history.snapshot["status"] == "ACTIVE"
