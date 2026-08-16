from datetime import date
from typing import Optional
from sqlalchemy import Boolean, Date, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column
from cartei_db.base import Base


class TenantRoomAssignment(Base):
    __tablename__ = "tenant_room_assignment"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    tenant_id: Mapped[int] = mapped_column(ForeignKey("tenant.id"), nullable=False)
    room_id: Mapped[int] = mapped_column(ForeignKey("room.id"), nullable=False)
    moved_in: Mapped[date] = mapped_column(Date, nullable=False)
    moved_out: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    mailbox_key: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_sublet: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    sublet_of_tenant_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("tenant.id"), nullable=True
    )
    key_received: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    key_returned: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    deposit_iban: Mapped[Optional[str]] = mapped_column(String, nullable=True)
