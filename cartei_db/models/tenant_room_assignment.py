from datetime import date
from typing import Optional
from sqlalchemy import Date, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column
from cartei_db.base import Base


class TenantRoomAssignment(Base):
    __tablename__ = "tenant_room_assignment"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    tenant_id: Mapped[int] = mapped_column(ForeignKey("tenant.id"), nullable=False)
    room_id: Mapped[int] = mapped_column(ForeignKey("room.id"), nullable=False)
    moved_in: Mapped[date] = mapped_column(Date, nullable=False)
    moved_out: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
