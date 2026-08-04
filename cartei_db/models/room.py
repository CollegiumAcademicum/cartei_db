from decimal import Decimal
from sqlalchemy import Boolean, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column
from cartei_db.base import Base, Historized


class Room(Historized, Base):
    __tablename__ = "room"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    wg_id: Mapped[int] = mapped_column(ForeignKey("wg.id"), nullable=False)
    name: Mapped[str] = mapped_column(String, nullable=False)
    size_sqm: Mapped[Decimal] = mapped_column(Numeric(8, 2), nullable=False)
    has_mattress: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    has_bed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    has_table: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    has_closet: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    freifinanziert: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
