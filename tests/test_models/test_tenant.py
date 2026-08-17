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
        barrier_free_needed=False,
        mailbox_list_opt_in=False, soli_miete_wunsch=Decimal("0"),
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


def test_soli_miete_wunsch_can_be_negative(session):
    t = _tenant(soli_miete_wunsch=Decimal("-15.00"))
    session.add(t)
    session.flush()
    assert session.get(Tenant, t.id).soli_miete_wunsch == Decimal("-15.00")
