from sqlalchemy import ForeignKey, Integer, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from cartei_db.base import Base


class DocumentSigner(Base):
    __tablename__ = "document_signer"
    __table_args__ = (
        UniqueConstraint("document_id", "tenant_id", name="uq_document_signer_document_tenant"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    document_id: Mapped[int] = mapped_column(ForeignKey("document.id"), nullable=False)
    tenant_id: Mapped[int] = mapped_column(ForeignKey("tenant.id"), nullable=False)
