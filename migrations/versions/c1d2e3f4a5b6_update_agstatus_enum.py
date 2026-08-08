"""update agstatus enum to new engagement categories

Revision ID: c1d2e3f4a5b6
Revises: a1b2c3d4e5f6
Create Date: 2026-08-08 15:20:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "c1d2e3f4a5b6"
down_revision: Union[str, Sequence[str], None] = "a1b2c3d4e5f6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_OLD_VALUES = ("ACTIVE", "NOT_ACTIVE_ENOUGH", "CONTACTED", "INACTIVE")
_NEW_VALUES = ("ZU_AKTIV", "AKTIV", "NICHT_AUSREICHEND", "IM_GESPRAECH", "INAKTIV")


def upgrade() -> None:
    # Detach column from enum so we can replace the type
    op.execute("ALTER TABLE ag_abfrage_result ALTER COLUMN status TYPE text USING status::text")

    # Migrate existing rows to new values
    op.execute("""
        UPDATE ag_abfrage_result SET status = CASE status
            WHEN 'ACTIVE'            THEN 'AKTIV'
            WHEN 'NOT_ACTIVE_ENOUGH' THEN 'NICHT_AUSREICHEND'
            WHEN 'CONTACTED'         THEN 'IM_GESPRAECH'
            WHEN 'INACTIVE'          THEN 'INAKTIV'
            ELSE status
        END
    """)

    op.execute("DROP TYPE agstatus")
    op.execute("CREATE TYPE agstatus AS ENUM ('ZU_AKTIV', 'AKTIV', 'NICHT_AUSREICHEND', 'IM_GESPRAECH', 'INAKTIV')")
    op.execute("ALTER TABLE ag_abfrage_result ALTER COLUMN status TYPE agstatus USING status::agstatus")


def downgrade() -> None:
    op.execute("ALTER TABLE ag_abfrage_result ALTER COLUMN status TYPE text USING status::text")

    op.execute("""
        UPDATE ag_abfrage_result SET status = CASE status
            WHEN 'AKTIV'             THEN 'ACTIVE'
            WHEN 'ZU_AKTIV'          THEN 'ACTIVE'
            WHEN 'NICHT_AUSREICHEND' THEN 'NOT_ACTIVE_ENOUGH'
            WHEN 'IM_GESPRAECH'      THEN 'CONTACTED'
            WHEN 'INAKTIV'           THEN 'INACTIVE'
            ELSE status
        END
    """)

    op.execute("DROP TYPE agstatus")
    op.execute("CREATE TYPE agstatus AS ENUM ('ACTIVE', 'NOT_ACTIVE_ENOUGH', 'CONTACTED', 'INACTIVE')")
    op.execute("ALTER TABLE ag_abfrage_result ALTER COLUMN status TYPE agstatus USING status::agstatus")
