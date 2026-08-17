from datetime import date

from sqlalchemy import Date, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from cartei_db.base import Base
from cartei_db.models.document_base import RoomAssignmentDocumentColumns


class WohnungsgeberbescheinigungDocument(RoomAssignmentDocumentColumns, Base):
    __tablename__ = "wohnungsgeberbescheinigung_document"

    signed_at: Mapped[date] = mapped_column(Date, nullable=False)
    company_signed_by_id: Mapped[int] = mapped_column(ForeignKey("tenant.id"), nullable=False)
