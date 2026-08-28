import uuid
from datetime import date
from decimal import Decimal
from typing import Optional

from sqlalchemy import Boolean, Date, Integer, Numeric, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from cartei_db.base import Base, Historized


class Tenant(Historized, Base):
    __tablename__ = "tenant"
    __history_exclude__ = {"is_flinta"}

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    first_name: Mapped[str] = mapped_column(String, nullable=False)
    last_name: Mapped[str] = mapped_column(String, nullable=False)
    email: Mapped[str] = mapped_column(String, nullable=False)
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
    soli_miete_wunsch: Mapped[Decimal] = mapped_column(
        Numeric(10, 2), nullable=False, default=Decimal("0")
    )
    # Ersteinzug/Auszug are derived from tenant_room_assignment (earliest moved_in /
    # latest moved_out once no assignment is open) — no stored columns.
    comments: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
