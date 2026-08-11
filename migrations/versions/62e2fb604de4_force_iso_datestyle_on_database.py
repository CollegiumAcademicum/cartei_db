"""force iso datestyle on database

Revision ID: 62e2fb604de4
Revises: 75b185c2506d
Create Date: 2026-08-11 10:57:21.003653

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = '62e2fb604de4'
down_revision: Union[str, Sequence[str], None] = '75b185c2506d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# Pin ISO date output and YMD input parsing at the database level, independent of
# any client's locale. Scoped to the current database via current_database() so it
# is portable across dev/prod DB names. Takes effect on new connections.
def upgrade() -> None:
    op.execute(
        "DO $$ BEGIN "
        "EXECUTE format('ALTER DATABASE %I SET datestyle = %L', current_database(), 'ISO, YMD'); "
        "END $$;"
    )


def downgrade() -> None:
    op.execute(
        "DO $$ BEGIN "
        "EXECUTE format('ALTER DATABASE %I RESET datestyle', current_database()); "
        "END $$;"
    )
