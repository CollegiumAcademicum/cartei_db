import contextvars
import uuid
from datetime import date, datetime, timezone
from decimal import Decimal
from typing import Any

from sqlalchemy import DateTime, Integer, String, event
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from cartei_db.enums import ChangeSource

changed_by_var: contextvars.ContextVar[str] = contextvars.ContextVar(
    "changed_by", default="system"
)
change_source_var: contextvars.ContextVar[ChangeSource] = contextvars.ContextVar(
    "change_source", default=ChangeSource.SERVICE
)


class Base(DeclarativeBase):
    pass


class EntityHistory(Base):
    __tablename__ = "entity_history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    entity_type: Mapped[str] = mapped_column(String, nullable=False, index=True)
    entity_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    snapshot: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    changed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    changed_by: Mapped[str] = mapped_column(String, nullable=False)
    change_source: Mapped[str] = mapped_column(String, nullable=False)


def _jsonify(value: Any) -> Any:
    if value is None or isinstance(value, (bool, int, float, str)):
        return value
    if isinstance(value, datetime):  # must precede date check (datetime subclasses date)
        return value.isoformat()
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, uuid.UUID):
        return str(value)
    if hasattr(value, "value"):  # enum
        return value.value
    return str(value)


def _write_to_history(connection, tablename: str, entity_id: int, snapshot: dict[str, Any]) -> None:
    connection.execute(
        EntityHistory.__table__.insert().values(
            entity_type=tablename,
            entity_id=entity_id,
            snapshot=snapshot,
            changed_at=datetime.now(timezone.utc),
            changed_by=changed_by_var.get(),
            change_source=change_source_var.get().value,
        )
    )


def _on_update(mapper, connection, target) -> None:
    from sqlalchemy import inspect as sa_inspect

    exclude = getattr(target.__class__, "__history_exclude__", set())
    insp = sa_inspect(target)
    snapshot: dict[str, Any] = {}

    for col in mapper.columns:
        if col.key in exclude:
            continue
        attr = insp.attrs[col.key]
        hist = attr.history
        # history.deleted holds the old value when an attribute was changed
        if hist.deleted:
            value = hist.deleted[0]
        elif hist.unchanged:
            value = hist.unchanged[0]
        else:
            value = getattr(target, col.key)
        snapshot[col.key] = _jsonify(value)

    _write_to_history(connection, target.__tablename__, target.id, snapshot)


def _on_delete(mapper, connection, target) -> None:
    exclude = getattr(target.__class__, "__history_exclude__", set())
    snapshot = {
        col.key: _jsonify(getattr(target, col.key))
        for col in mapper.columns
        if col.key not in exclude
    }
    _write_to_history(connection, target.__tablename__, target.id, snapshot)


class Historized:
    __history_exclude__: set[str] = set()


event.listen(Historized, "before_update", _on_update, propagate=True)
event.listen(Historized, "before_delete", _on_delete, propagate=True)
