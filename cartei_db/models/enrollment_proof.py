from datetime import date, datetime
from typing import Optional
from sqlalchemy import Boolean, Date, DateTime, Enum as SAEnum, ForeignKey, Integer, LargeBinary, String
from sqlalchemy.orm import Mapped, mapped_column
from cartei_db.base import Base
from cartei_db.enums import EnrollmentType


class EnrollmentProof(Base):
    __tablename__ = "enrollment_proof"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    tenant_id: Mapped[int] = mapped_column(ForeignKey("tenant.id"), nullable=False)
    enrollment_type: Mapped[EnrollmentType] = mapped_column(SAEnum(EnrollmentType), nullable=False)
    field_of_study: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    educational_institution: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    file_name: Mapped[str] = mapped_column(String, nullable=False)
    file_data: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
    uploaded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    uploaded_by_id: Mapped[Optional[int]] = mapped_column(ForeignKey("tenant.id"), nullable=True)
    last_edited_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    last_edited_by_id: Mapped[Optional[int]] = mapped_column(ForeignKey("tenant.id"), nullable=True)
    valid_until: Mapped[date] = mapped_column(Date, nullable=False)
    verified_by_id: Mapped[Optional[int]] = mapped_column(ForeignKey("tenant.id"), nullable=True)
    verified_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    needs_human_review: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false")
