from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column

from cartei_db.base import Base, Historized


class Uebergabe(Historized, Base):
    """One room handover (Übergabe). A thin anchor: the room, the outgoing
    assignment (nullable — first occupancy has none), the inspector, and start
    / completion timestamps. Damages recorded during the handover are plain
    room_damage / wg_damage rows; the recap scopes them by the outgoing
    assignment's date window. No PDF / signed scan yet (deferred)."""

    __tablename__ = "uebergabe"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    room_id: Mapped[int] = mapped_column(ForeignKey("room.id"), nullable=False)
    tenant_room_assignment_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("tenant_room_assignment.id"), nullable=True)
    incoming_tenant_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("tenant.id"), nullable=True)
    conducted_by_id: Mapped[int] = mapped_column(ForeignKey("tenant.id"), nullable=False)
    conducted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    note: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
