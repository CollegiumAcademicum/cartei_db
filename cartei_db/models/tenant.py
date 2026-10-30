import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import Boolean, Date, DateTime, Integer, Numeric, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from cartei_db.base import Base, Historized


class Tenant(Historized, Base):
    __tablename__ = "tenant"
    __history_exclude__ = {"is_flinta", "email_refreshed_at"}

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    first_name: Mapped[str] = mapped_column(String, nullable=False)
    last_name: Mapped[str] = mapped_column(String, nullable=False)
    # Last known address. For a tenant with an intranet account FreeIPA `mail` is the
    # source of truth and this column is a read-through cache (refreshed at login and
    # before every send, written through on edit); for a tenant without one (before
    # provisioning, after the account is deleted) it is the only copy.
    email: Mapped[str] = mapped_column(String, nullable=False)
    # When `email` was last confirmed against FreeIPA; NULL = never.
    email_refreshed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    # LDAP account link — NULL for tenants added manually by Mietverwaltung before
    # an intranet account exists. unique() still permits many NULLs (each distinct).
    intranet_username: Mapped[Optional[str]] = mapped_column(String, nullable=True, unique=True)
    intranet_uuid: Mapped[Optional[uuid.UUID]] = mapped_column(Uuid, nullable=True, unique=True)
    preferred_name: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    pronouns: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    date_of_birth: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    phone: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    is_flinta: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false")
    barrier_free_needed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    mailbox_list_opt_in: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    profile_setup_completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    no_phone_number: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false")
    soli_miete_wunsch: Mapped[Decimal] = mapped_column(
        Numeric(10, 2), nullable=False, default=Decimal("0")
    )
    # Ersteinzug/Auszug are derived from tenant_room_assignment (earliest moved_in /
    # latest moved_out once no assignment is open) — no stored columns.
    comments: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
