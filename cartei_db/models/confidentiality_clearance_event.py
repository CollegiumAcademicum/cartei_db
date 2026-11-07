from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, Enum as SAEnum, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column

from cartei_db.base import Base
from cartei_db.enums import ConfidentialityClearanceAction


class ConfidentialityClearanceEvent(Base):
    """Append-only approval record for the FreeIPA group confidentiality_clearance:
    one row per grant, re-grant or revoke, tied to the Vertraulichkeitserklaerung
    document it rests on. actor_id NULL = legacy backfill (granted before this log
    existed). Immutable: a no-update/no-delete trigger enforces it for every role.
    Not Historized - it is itself the audit trail."""

    __tablename__ = "confidentiality_clearance_event"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    tenant_id: Mapped[int] = mapped_column(ForeignKey("tenant.id"), nullable=False, index=True)
    document_id: Mapped[int] = mapped_column(
        ForeignKey("vertraulichkeitserklaerung_document.id"), nullable=False, index=True
    )
    action: Mapped[ConfidentialityClearanceAction] = mapped_column(
        SAEnum(ConfidentialityClearanceAction), nullable=False
    )
    actor_id: Mapped[Optional[int]] = mapped_column(ForeignKey("tenant.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
