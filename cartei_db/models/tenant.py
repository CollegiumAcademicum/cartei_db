import uuid
from datetime import date
from decimal import Decimal
from typing import Optional

from sqlalchemy import Boolean, Date, ForeignKey, Integer, Numeric, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from cartei_db.base import Base, Historized


class Tenant(Historized, Base):
    __tablename__ = "tenant"
    __history_exclude__ = {"is_flinta"}

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    first_name: Mapped[str] = mapped_column(String, nullable=False)
    last_name: Mapped[str] = mapped_column(String, nullable=False)
    email: Mapped[str] = mapped_column(String, nullable=False)
    intranet_username: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    intranet_uuid: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False, unique=True)
    preferred_name: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    pronouns: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    date_of_birth: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    phone: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    is_flinta: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false")
    barrier_free_needed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    mailbox_key: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    mailbox_list_opt_in: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    soli_miete_wunsch: Mapped[Decimal] = mapped_column(
        Numeric(10, 2), nullable=False, default=Decimal("0")
    )
    is_sublet: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    sublet_from: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    sublet_to: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    sublet_of_tenant_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("tenant.id"), nullable=True
    )
    data_priv_signed_at: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    photo_allowance_signed_at: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    move_in: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    move_out: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    comments: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    sublet_of: Mapped[Optional["Tenant"]] = relationship(
        "Tenant", remote_side="Tenant.id", foreign_keys=[sublet_of_tenant_id]
    )
