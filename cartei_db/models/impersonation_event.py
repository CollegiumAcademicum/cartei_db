from datetime import datetime

from sqlalchemy import DateTime, Enum as SAEnum, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from cartei_db.base import Base
from cartei_db.enums import ImpersonationAction


class ImpersonationEvent(Base):
    """Append-only audit record of superuser impersonation. One row per start
    and per stop, so read-only impersonation sessions are traceable even when no
    data was written (the write-path attribution `x (als y)` only covers writes).
    Identity is the LDAP/intranet username (not a Tenant FK, so superuser/admin
    logins without a Tenant are recorded too). Immutable: a no-update/no-delete
    trigger enforces the invariant for every role. Not Historized — it is itself
    the audit trail."""

    __tablename__ = "impersonation_event"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    impersonator_username: Mapped[str] = mapped_column(String(150), nullable=False, index=True)
    target_username: Mapped[str] = mapped_column(String(150), nullable=False, index=True)
    action: Mapped[ImpersonationAction] = mapped_column(SAEnum(ImpersonationAction), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
