from typing import Optional

from sqlalchemy import Enum as SAEnum, ForeignKey, Integer, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from cartei_db.base import Base
from cartei_db.enums import DamageLine


class UebergabeProtokollDamage(Base):
    __tablename__ = "uebergabeprotokoll_damage"
    __table_args__ = (
        UniqueConstraint("protocol_id", "line", name="uq_uebergabeprotokoll_damage"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    protocol_id: Mapped[int] = mapped_column(ForeignKey("uebergabeprotokoll.id"), nullable=False)
    line: Mapped[DamageLine] = mapped_column(SAEnum(DamageLine), nullable=False)
    # Buckets: Flecken/Kleber use lt1/mid/gt (<1cm, 1-5cm, >5cm);
    # Löcher use lt1/gt only (<1cm, >1cm), mid stays 0.
    count_lt1: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    count_mid: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    count_gt: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    note: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    protocol: Mapped["UebergabeProtokoll"] = relationship(back_populates="damages")
