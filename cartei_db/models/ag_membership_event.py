from datetime import datetime

from sqlalchemy import DateTime, Enum as SAEnum, ForeignKey, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column

from cartei_db.base import Base
from cartei_db.enums import AGMembershipAction


class AGMembershipEvent(Base):
    """Append-only record of AG/INI self-service joins and leaves in FreeIPA
    (ag.* / in.* groups). Written after the FreeIPA change succeeded. No actor
    column: impersonation is refused, so the actor is always the tenant.
    Immutable via trigger. Not Historized - it is itself the audit trail."""

    __tablename__ = "ag_membership_event"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    tenant_id: Mapped[int] = mapped_column(ForeignKey("tenant.id"), nullable=False, index=True)
    uid: Mapped[str] = mapped_column(Text, nullable=False)
    group_cn: Mapped[str] = mapped_column(Text, nullable=False, index=True)
    action: Mapped[AGMembershipAction] = mapped_column(SAEnum(AGMembershipAction), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
