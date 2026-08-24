from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, Integer, LargeBinary, Text
from sqlalchemy.orm import Mapped, mapped_column


class DamageColumns:
    """Shared columns for the damage tables (room_damage, wg_damage). A
    declarative mixin so each concrete table gets its own copy; the target FK
    and the typed `line` column are declared per table. A damage is open while
    fixed_at IS NULL. Rows are never deleted; the only lifecycle mutation is
    setting fixed_at (fix) or clearing it (reopen). At most one photo per
    damage (photo_name/photo_data, both NULL when absent); re-uploading
    replaces it."""

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    size: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    note: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_by_id: Mapped[int] = mapped_column(ForeignKey("tenant.id"), nullable=False)
    fixed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    fixed_by_id: Mapped[Optional[int]] = mapped_column(ForeignKey("tenant.id"), nullable=True)
    photo_name: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    photo_data: Mapped[Optional[bytes]] = mapped_column(LargeBinary, nullable=True)
