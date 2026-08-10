import contextvars
from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, Index, Integer, String, event
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, Session

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
    __table_args__ = (
        Index("ix_entity_history_type_id", "entity_type", "entity_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    entity_type: Mapped[str] = mapped_column(String, nullable=False, index=True)
    entity_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    snapshot: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    changed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    changed_by: Mapped[str] = mapped_column(String, nullable=False)
    change_source: Mapped[str] = mapped_column(String, nullable=False)


class Historized:
    __history_exclude__: set[str] = set()


AUDIT_FUNCTION_SQL = """
CREATE OR REPLACE FUNCTION audit_history() RETURNS trigger AS $$
DECLARE
    snap jsonb;
    col  text;
BEGIN
    snap := to_jsonb(OLD);
    FOREACH col IN ARRAY coalesce(TG_ARGV, '{}') LOOP
        snap := snap - col;
    END LOOP;
    INSERT INTO entity_history(entity_type, entity_id, snapshot, changed_at, changed_by, change_source)
    VALUES (
        TG_TABLE_NAME, OLD.id, snap, now(),
        coalesce(current_setting('cartei.changed_by', true), 'system'),
        coalesce(current_setting('cartei.change_source', true), 'SERVICE')
    );
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;
"""


def create_audit_trigger_sql(table: str, exclude: set[str] = frozenset()) -> str:
    args = ", ".join(repr(c) for c in sorted(exclude))
    return (
        f"CREATE TRIGGER {table}_audit AFTER UPDATE OR DELETE ON {table} "
        f"FOR EACH ROW EXECUTE FUNCTION audit_history({args});"
    )


def drop_audit_trigger_sql(table: str) -> str:
    return f"DROP TRIGGER IF EXISTS {table}_audit ON {table};"


@event.listens_for(Session, "after_begin")
def _set_audit_actor(session, transaction, connection) -> None:
    connection.exec_driver_sql(
        "SELECT set_config('cartei.changed_by', %s, true)", (changed_by_var.get(),)
    )
    connection.exec_driver_sql(
        "SELECT set_config('cartei.change_source', %s, true)",
        (change_source_var.get().value,),
    )
