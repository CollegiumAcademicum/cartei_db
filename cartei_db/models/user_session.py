from datetime import datetime

from sqlalchemy import DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from cartei_db.base import Base


class UserSession(Base):
    """Login-time metadata for a Django web session, so admins can list a
    user's active devices and revoke one (or all). Keyed to the Django session
    by `session_key`; identity is the LDAP/intranet username (not a Tenant FK,
    so non-tenant logins like admins are tracked too). Written by CArtei's
    `user_logged_in` signal; the row is a snapshot at login (IP, user agent),
    not kept live. Not Historized — session churn shouldn't spam entity_history."""

    __tablename__ = "user_session"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    session_key: Mapped[str] = mapped_column(String(40), nullable=False, unique=True)
    username: Mapped[str] = mapped_column(String(150), nullable=False, index=True)
    ip_address: Mapped[str | None] = mapped_column(String(45), nullable=True)
    user_agent: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
