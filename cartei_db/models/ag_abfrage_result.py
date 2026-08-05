from typing import Optional
from sqlalchemy import Enum as SAEnum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from cartei_db.base import Base, Historized
from cartei_db.enums import AGStatus


class AGAbfrageResult(Historized, Base):
    __tablename__ = "ag_abfrage_result"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    abfrage_id: Mapped[int] = mapped_column(ForeignKey("ag_abfrage.id"), nullable=False)
    ag_name: Mapped[str] = mapped_column(String, nullable=False)
    tenant_id: Mapped[int] = mapped_column(ForeignKey("tenant.id"), nullable=False)
    status: Mapped[AGStatus] = mapped_column(SAEnum(AGStatus), nullable=False)
    note: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
