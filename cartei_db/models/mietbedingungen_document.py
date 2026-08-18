from datetime import date

from sqlalchemy import Date
from sqlalchemy.orm import Mapped, mapped_column

from cartei_db.base import Base
from cartei_db.models.document_base import RoomAssignmentDocumentColumns


class MietbedingungenDocument(RoomAssignmentDocumentColumns, Base):
    __tablename__ = "mietbedingungen_document"

    signed_at: Mapped[date] = mapped_column(Date, nullable=False)
