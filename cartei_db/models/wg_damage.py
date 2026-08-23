from typing import Optional

from sqlalchemy import Enum as SAEnum, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column

from cartei_db.base import Base
from cartei_db.enums import DamageSize, WGDamageLine
from cartei_db.models.damage_base import DamageColumns


class WGDamage(DamageColumns, Base):
    __tablename__ = "wg_damage"

    wg_id: Mapped[int] = mapped_column(ForeignKey("wg.id"), nullable=False)
    line: Mapped[WGDamageLine] = mapped_column(SAEnum(WGDamageLine), nullable=False)
    size: Mapped[Optional[DamageSize]] = mapped_column(SAEnum(DamageSize), nullable=True)
