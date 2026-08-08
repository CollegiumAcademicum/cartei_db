from sqlalchemy import CheckConstraint, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from cartei_db.base import Base

VALID_CLUSTERS = ["0A", "0B", "1A", "1B", "1C", "1D", "2A", "2B", "2C", "2D", "3A", "3B", "3C", "3D"]


class WG(Base):
    __tablename__ = "wg"
    __table_args__ = (
        CheckConstraint(f"cluster IN ({', '.join(repr(c) for c in VALID_CLUSTERS)})", name="wg_cluster_valid"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    building_id: Mapped[int] = mapped_column(ForeignKey("building.id"), nullable=False)
    name: Mapped[str] = mapped_column(String, nullable=False)
    cluster: Mapped[str | None] = mapped_column(String(3), nullable=True)
