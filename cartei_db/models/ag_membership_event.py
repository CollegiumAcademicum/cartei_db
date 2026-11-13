from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, Enum as SAEnum, ForeignKey, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column

from cartei_db.base import Base
from cartei_db.enums import AGMembershipAction


class AGMembershipEvent(Base):
    """Append-only record of AG/INI joins and leaves in FreeIPA (ag.* / in.*
    groups), from dashboard self-service or an AG's engagement check. Written
    after the FreeIPA change succeeded. uid/tenant_id = whose membership changed
    (tenant_id NULL: an LDAP member without a tenant row); actor_username = who
    acted (the real person when impersonating). Immutable via trigger. Not
    Historized - it is itself the audit trail."""

    __tablename__ = "ag_membership_event"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    tenant_id: Mapped[Optional[int]] = mapped_column(ForeignKey("tenant.id"), nullable=True, index=True)
    uid: Mapped[str] = mapped_column(Text, nullable=False)
    group_cn: Mapped[str] = mapped_column(Text, nullable=False, index=True)
    action: Mapped[AGMembershipAction] = mapped_column(SAEnum(AGMembershipAction), nullable=False)
    actor_username: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
