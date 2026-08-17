from typing import Optional
from sqlalchemy import Enum as SAEnum, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from cartei_db.base import Base, Historized
from cartei_db.enums import AGHealth


class AGAbfrageHealth(Historized, Base):
    """Overall self-reported health of one AG for one Abfrage (not per member)."""
    __tablename__ = "ag_abfrage_health"
    __table_args__ = (UniqueConstraint("abfrage_id", "ag_name", name="uq_ag_abfrage_health"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    abfrage_id: Mapped[int] = mapped_column(ForeignKey("ag_abfrage.id"), nullable=False)
    ag_name: Mapped[str] = mapped_column(String, nullable=False)
    health: Mapped[AGHealth] = mapped_column(SAEnum(AGHealth), nullable=False)
    note: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
