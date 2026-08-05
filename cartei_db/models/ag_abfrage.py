from datetime import date
from typing import Optional
from sqlalchemy import Date, Integer, String
from sqlalchemy.orm import Mapped, mapped_column
from cartei_db.base import Base


class AGAbfrage(Base):
    __tablename__ = "ag_abfrage"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    date: Mapped[date] = mapped_column(Date, nullable=False)
    label: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    ends_at: Mapped[date] = mapped_column(Date, nullable=False)
    grace_ends_at: Mapped[date] = mapped_column(Date, nullable=False)
