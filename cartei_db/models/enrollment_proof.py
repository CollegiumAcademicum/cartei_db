from datetime import date, datetime
from sqlalchemy import Date, DateTime, Enum as SAEnum, ForeignKey, Integer, LargeBinary, String
from sqlalchemy.orm import Mapped, mapped_column
from cartei_db.base import Base
from cartei_db.enums import EnrollmentType


class EnrollmentProof(Base):
    __tablename__ = "enrollment_proof"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    tenant_id: Mapped[int] = mapped_column(ForeignKey("tenant.id"), nullable=False)
    enrollment_type: Mapped[EnrollmentType] = mapped_column(
        SAEnum(EnrollmentType), nullable=False
    )
    enrollment_name: Mapped[str] = mapped_column(String, nullable=False)
    file_data: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
    file_name: Mapped[str] = mapped_column(String, nullable=False)
    submitted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    valid_until: Mapped[date] = mapped_column(Date, nullable=False)
