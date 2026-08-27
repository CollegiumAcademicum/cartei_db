from datetime import date

from sqlalchemy import Date, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from cartei_db.base import Base
from cartei_db.models.document_base import TenantDocumentColumns


class MietvertragDocument(TenantDocumentColumns, Base):
    __tablename__ = "mietvertrag_document"

    renter_signed_at: Mapped[date] = mapped_column(Date, nullable=False)
    company_signed_at: Mapped[date] = mapped_column(Date, nullable=False)
    company_signed_by_id: Mapped[int] = mapped_column(ForeignKey("tenant.id"), nullable=False)
