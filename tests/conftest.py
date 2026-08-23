import os
import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

from cartei_db.base import (
    Base, Historized, AUDIT_FUNCTION_SQL, create_audit_trigger_sql,
)


@pytest.fixture(scope="session")
def engine():
    # Models are registered in Base.metadata as pytest collects test files.
    # Session-scoped fixture runs after all modules are imported.
    eng = create_engine(os.environ["DATABASE_URL"])
    # Drop first so a crashed prior run's leftover tables/rows can't poison this one.
    Base.metadata.drop_all(eng)
    Base.metadata.create_all(eng)
    with eng.begin() as conn:
        conn.execute(text(AUDIT_FUNCTION_SQL))
        for cls in Historized.__subclasses__():
            conn.execute(text(create_audit_trigger_sql(
                cls.__tablename__, getattr(cls, "__history_exclude__", set())
            )))
        from cartei_db.document_triggers import document_append_only_sql
        for stmt in document_append_only_sql():
            conn.execute(text(stmt))
        from cartei_db.damage_triggers import damage_no_delete_sql
        for stmt in damage_no_delete_sql():
            conn.execute(text(stmt))
    yield eng
    Base.metadata.drop_all(eng)
    with eng.begin() as conn:
        conn.execute(text("DROP FUNCTION IF EXISTS audit_history() CASCADE"))
        conn.execute(text("DROP FUNCTION IF EXISTS damage_no_delete() CASCADE"))
    eng.dispose()


@pytest.fixture
def session(engine):
    connection = engine.connect()
    transaction = connection.begin()
    sess = Session(connection, join_transaction_mode="create_savepoint")
    yield sess
    sess.close()
    transaction.rollback()
    connection.close()
