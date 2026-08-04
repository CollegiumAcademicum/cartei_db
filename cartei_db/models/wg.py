from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from cartei_db.base import Base


class WG(Base):
    __tablename__ = "wg"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    building_id: Mapped[int] = mapped_column(ForeignKey("building.id"), nullable=False)
    name: Mapped[str] = mapped_column(String, nullable=False)
