import uuid
from datetime import date, datetime, timezone
from decimal import Decimal
import pytest
from cartei_db.models.internal_note import InternalNote
from cartei_db.models.tenant import Tenant


@pytest.fixture
def author(session):
    t = Tenant(
        first_name="Anna", last_name="Schreiber", email="a@ca.de",
        intranet_username="aschreiber", intranet_uuid=uuid.uuid4(),
        is_flinta=False, barrier_free_needed=False,
        mailbox_list_opt_in=False, soli_miete_wunsch=Decimal("0"),
    )
    session.add(t)
    session.flush()
    return t


def test_create_internal_note(session, author):
    note = InternalNote(
        body="Testnotiz",
        source_group="clustersprechende",
        subject_type="tenant",
        subject_id=author.id,
        created_at=datetime(2026, 8, 12, 12, 0, tzinfo=timezone.utc),
        created_by_id=author.id,
    )
    session.add(note)
    session.flush()
    assert note.id is not None
    assert note.deleted_at is None
    assert note.deleted_by_id is None


def test_soft_delete(session, author):
    note = InternalNote(
        body="Zu löschen",
        source_group="mietverwaltung",
        subject_type="tenant",
        subject_id=author.id,
        created_at=datetime(2026, 8, 12, 12, 0, tzinfo=timezone.utc),
        created_by_id=author.id,
    )
    session.add(note)
    session.flush()
    note.deleted_at = datetime(2026, 8, 12, 13, 0, tzinfo=timezone.utc)
    note.deleted_by_id = author.id
    session.flush()
    assert note.deleted_at is not None
