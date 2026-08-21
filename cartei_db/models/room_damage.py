from typing import Optional

from sqlalchemy import Enum as SAEnum, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column

from cartei_db.base import Base
from cartei_db.enums import DamageSize, RoomDamageLine
from cartei_db.models.damage_base import DamageColumns


class RoomDamage(DamageColumns, Base):
    __tablename__ = "room_damage"

    room_id: Mapped[int] = mapped_column(ForeignKey("room.id"), nullable=False)
    line: Mapped[RoomDamageLine] = mapped_column(SAEnum(RoomDamageLine), nullable=False)
    size: Mapped[Optional[DamageSize]] = mapped_column(SAEnum(DamageSize), nullable=True)
