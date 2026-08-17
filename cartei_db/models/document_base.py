from datetime import date, datetime
from typing import Optional

from sqlalchemy import Date, DateTime, ForeignKey, Integer, LargeBinary, String, Text
from sqlalchemy.orm import Mapped, mapped_column


class DocumentColumns:
    """Shared columns for every per-type signed-document table
    (datenschutz_document, photoerlaubnis_document, ...). A declarative mixin so
    each concrete table gets its own copy and is free to add type-specific
    columns without touching the others. Append-only: the only mutation allowed
    is a single revocation, enforced by the per-table trigger in
    document_triggers.py."""

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    tenant_id: Mapped[int] = mapped_column(ForeignKey("tenant.id"), nullable=False)
    file_name: Mapped[str] = mapped_column(String, nullable=False)
    file_data: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
    signed_at: Mapped[date] = mapped_column(Date, nullable=False)
    uploaded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    uploaded_by_id: Mapped[int] = mapped_column(ForeignKey("tenant.id"), nullable=False)
    revoked_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    revoked_by_id: Mapped[Optional[int]] = mapped_column(ForeignKey("tenant.id"), nullable=True)
    revoked_note: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
