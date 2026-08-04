import os
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session


@pytest.fixture(scope="session")
def engine():
    from cartei_db.base import Base
    # Models are registered in Base.metadata as pytest collects test files.
    # Session-scoped fixture runs after all modules are imported.
    eng = create_engine(os.environ["DATABASE_URL"])
    Base.metadata.create_all(eng)
    yield eng
    Base.metadata.drop_all(eng)
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
