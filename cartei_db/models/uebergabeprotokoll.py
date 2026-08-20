from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, Enum as SAEnum, ForeignKey, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from cartei_db.base import Base, Historized
from cartei_db.enums import (
    FurnitureSource, MattressSource, PartitionPosition, UebergabeProtokollType,
)


class UebergabeProtokoll(Historized, Base):
    __tablename__ = "uebergabeprotokoll"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    tenant_room_assignment_id: Mapped[int] = mapped_column(
        ForeignKey("tenant_room_assignment.id"), nullable=False
    )
    protocol_type: Mapped[UebergabeProtokollType] = mapped_column(
        SAEnum(UebergabeProtokollType), nullable=False
    )
    # Draft-nullable: filled on step 1, required before PDF generation.
    mv_representative_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("tenant.id"), nullable=True
    )
    protocol_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    partition_position: Mapped[Optional[PartitionPosition]] = mapped_column(
        SAEnum(PartitionPosition), nullable=True
    )
    barrierefrei: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    bed_source: Mapped[Optional[FurnitureSource]] = mapped_column(SAEnum(FurnitureSource), nullable=True)
    mattress_source: Mapped[Optional[MattressSource]] = mapped_column(SAEnum(MattressSource), nullable=True)
    desk_source: Mapped[Optional[FurnitureSource]] = mapped_column(SAEnum(FurnitureSource), nullable=True)
    closet_source: Mapped[Optional[FurnitureSource]] = mapped_column(SAEnum(FurnitureSource), nullable=True)

    sonstige_schaeden: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    sonstige_moebel: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    kueche_schaeden: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    bad_schaeden: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    gemeinschaftsflaeche: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    finalized_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    damages: Mapped[list["UebergabeProtokollDamage"]] = relationship(
        back_populates="protocol", order_by="UebergabeProtokollDamage.line",
    )
