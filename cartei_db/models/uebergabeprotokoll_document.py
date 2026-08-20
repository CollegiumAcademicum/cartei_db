from typing import Optional

from sqlalchemy import ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column

from cartei_db.base import Base
from cartei_db.models.document_base import RoomAssignmentDocumentColumns


class UebergabeProtokollDocument(RoomAssignmentDocumentColumns, Base):
    __tablename__ = "uebergabeprotokoll_document"

    uebergabeprotokoll_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("uebergabeprotokoll.id"), nullable=True
    )
