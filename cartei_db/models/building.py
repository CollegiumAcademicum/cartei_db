from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from cartei_db.base import Base


class Building(Base):
    __tablename__ = "building"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String, nullable=False, unique=True)
