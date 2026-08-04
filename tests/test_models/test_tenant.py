import uuid
from datetime import date
from decimal import Decimal
from cartei_db.models.tenant import Tenant
from cartei_db.base import EntityHistory


def _tenant(**overrides) -> Tenant:
    defaults = dict(
        first_name="Anna", last_name="Muster",
        email="anna@example.com", intranet_username="amuster",
        intranet_uuid=uuid.uuid4(), is_flinta=True,
        barrier_free_needed=False, mailbox_key=False,
        mailbox_list_opt_in=False, soli_miete_wunsch=Decimal("0"),
        is_sublet=False, move_in=date(2023, 9, 1),
    )
    defaults.update(overrides)
    return Tenant(**defaults)


def test_create_tenant(session):
    t = _tenant()
    session.add(t)
    session.flush()
    assert t.id is not None


def test_update_email_writes_history(session):
    t = _tenant(email="old@example.com")
    session.add(t)
    session.flush()
    t.email = "new@example.com"
    session.flush()
    history = session.query(EntityHistory).filter_by(
        entity_type="tenant", entity_id=t.id
    ).one()
    assert history.snapshot["email"] == "old@example.com"


def test_is_flinta_excluded_from_history(session):
    t = _tenant(is_flinta=True)
    session.add(t)
    session.flush()
    t.email = "changed@example.com"
    t.is_flinta = False
    session.flush()
    history = session.query(EntityHistory).filter_by(
        entity_type="tenant", entity_id=t.id
    ).one()
    assert "is_flinta" not in history.snapshot


def test_sublet_references_primary_tenant(session):
    primary = _tenant(intranet_username="primary", intranet_uuid=uuid.uuid4())
    session.add(primary)
    session.flush()
    sub = _tenant(
        intranet_username="subtenant", intranet_uuid=uuid.uuid4(),
        email="sub@example.com", is_sublet=True,
        sublet_from=date(2024, 1, 1), sublet_to=date(2024, 6, 30),
        sublet_of_tenant_id=primary.id,
    )
    session.add(sub)
    session.flush()
    assert sub.sublet_of_tenant_id == primary.id


def test_soli_miete_wunsch_can_be_negative(session):
    t = _tenant(soli_miete_wunsch=Decimal("-15.00"))
    session.add(t)
    session.flush()
    assert session.get(Tenant, t.id).soli_miete_wunsch == Decimal("-15.00")
