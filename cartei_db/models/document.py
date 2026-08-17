from datetime import date, datetime
from typing import Optional

from sqlalchemy import (
    Date, DateTime, Enum as SAEnum, ForeignKey, Integer, LargeBinary, String, Text,
)
from sqlalchemy.orm import Mapped, mapped_column

from cartei_db.base import Base
from cartei_db.enums import DocumentType


class Document(Base):
    __tablename__ = "document"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    tenant_id: Mapped[int] = mapped_column(ForeignKey("tenant.id"), nullable=False)
    document_type: Mapped[DocumentType] = mapped_column(SAEnum(DocumentType), nullable=False)
    file_name: Mapped[str] = mapped_column(String, nullable=False)
    file_data: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
    signed_at: Mapped[date] = mapped_column(Date, nullable=False)
    uploaded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    uploaded_by_id: Mapped[int] = mapped_column(ForeignKey("tenant.id"), nullable=False)
    revoked_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    revoked_by_id: Mapped[Optional[int]] = mapped_column(ForeignKey("tenant.id"), nullable=True)
    revoked_note: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
