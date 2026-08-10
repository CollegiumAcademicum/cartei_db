from sqlalchemy import Column, Integer, String

from cartei_db.base import Base, EntityHistory, Historized, changed_by_var, change_source_var
from cartei_db.enums import ChangeSource


class _Thing(Historized, Base):
    __tablename__ = "_test_thing"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String)
    secret = Column(String)
    __history_exclude__ = {"secret"}


def test_context_var_defaults():
    assert changed_by_var.get() == "system"
    assert change_source_var.get() == ChangeSource.SERVICE


def test_history_written_on_update(session):
    thing = _Thing(name="original", secret="hidden")
    session.add(thing)
    session.flush()

    thing.name = "updated"
    session.flush()

    rows = session.query(EntityHistory).filter_by(
        entity_type="_test_thing", entity_id=thing.id
    ).all()
    assert len(rows) == 1
    assert rows[0].snapshot["name"] == "original"   # old value
    assert "secret" not in rows[0].snapshot          # excluded column
    assert rows[0].changed_by == "system"            # default when unset
    assert rows[0].change_source == "SERVICE"


def test_history_written_on_delete(session):
    thing = _Thing(name="to_delete", secret="hidden")
    session.add(thing)
    session.flush()

    session.delete(thing)
    session.flush()

    row = session.query(EntityHistory).filter_by(
        entity_type="_test_thing", entity_id=thing.id
    ).one()
    assert row.snapshot["name"] == "to_delete"
    assert "secret" not in row.snapshot


def test_actor_from_context_var(session):
    token = changed_by_var.set("pbartz")
    src = change_source_var.set(ChangeSource.HUMAN)
    try:
        thing = _Thing(name="test")
        session.add(thing)
        session.flush()
        thing.name = "changed"
        session.flush()
        row = session.query(EntityHistory).filter_by(
            entity_type="_test_thing", entity_id=thing.id
        ).one()
        assert row.changed_by == "pbartz"
        assert row.change_source == "HUMAN"
    finally:
        changed_by_var.reset(token)
        change_source_var.reset(src)
