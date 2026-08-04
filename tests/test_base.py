import uuid
from datetime import date, datetime, timezone
from decimal import Decimal

import pytest
from sqlalchemy import Column, Integer, String

from cartei_db.base import (
    Base, EntityHistory, Historized,
    changed_by_var, change_source_var, _jsonify,
)
from cartei_db.enums import ChangeSource


# Minimal model registered in Base.metadata at collection time.
# pytest imports all test modules before running session-scoped fixtures,
# so this class will be in Base.metadata when engine.create_all() runs.
class _Thing(Historized, Base):
    __tablename__ = "_test_thing"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String)
    secret = Column(String)
    __history_exclude__ = {"secret"}


def test_context_var_defaults():
    assert changed_by_var.get() == "system"
    assert change_source_var.get() == ChangeSource.SERVICE


def test_jsonify_primitives():
    assert _jsonify(None) is None
    assert _jsonify(True) is True
    assert _jsonify(42) == 42
    assert _jsonify(3.14) == 3.14
    assert _jsonify("hello") == "hello"


def test_jsonify_datetime():
    dt = datetime(2024, 1, 15, 12, 0, tzinfo=timezone.utc)
    assert _jsonify(dt) == "2024-01-15T12:00:00+00:00"


def test_jsonify_date():
    assert _jsonify(date(2024, 1, 15)) == "2024-01-15"


def test_jsonify_decimal():
    assert _jsonify(Decimal("12.50")) == "12.50"


def test_jsonify_uuid():
    u = uuid.UUID("12345678-1234-5678-1234-567812345678")
    assert _jsonify(u) == "12345678-1234-5678-1234-567812345678"


def test_jsonify_enum():
    assert _jsonify(ChangeSource.HUMAN) == "HUMAN"


def test_history_written_on_update(session):
    thing = _Thing(name="original", secret="hidden")
    session.add(thing)
    session.flush()

    thing.name = "updated"
    thing.secret = "new_secret"
    session.flush()

    history = session.query(EntityHistory).filter_by(
        entity_type="_test_thing", entity_id=thing.id
    ).one()
    assert history.snapshot["name"] == "original"
    assert "secret" not in history.snapshot
    assert history.changed_by == "system"
    assert history.change_source == "SERVICE"


def test_history_written_on_delete(session):
    thing = _Thing(name="to_delete", secret="hidden")
    session.add(thing)
    session.flush()

    session.delete(thing)
    session.flush()

    history = session.query(EntityHistory).filter_by(
        entity_type="_test_thing", entity_id=thing.id
    ).one()
    assert history.snapshot["name"] == "to_delete"
    assert "secret" not in history.snapshot


def test_changed_by_context_var(session):
    token = changed_by_var.set("pbartz")
    try:
        thing = _Thing(name="test")
        session.add(thing)
        session.flush()
        thing.name = "changed"
        session.flush()
        history = session.query(EntityHistory).filter_by(
            entity_type="_test_thing", entity_id=thing.id
        ).one()
        assert history.changed_by == "pbartz"
    finally:
        changed_by_var.reset(token)
