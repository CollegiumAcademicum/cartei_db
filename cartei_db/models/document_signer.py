from sqlalchemy import ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from cartei_db.base import Base


class DocumentSigner(Base):
    """A tenant who signed a document. Shared across every per-type document
    table via a polymorphic reference (document_type + document_id), mirroring
    InternalNote's subject_type/subject_id. document_id has no FK — it can point
    at any of the document tables — so signer integrity is enforced in the app
    layer, as it is for notes."""

    __tablename__ = "document_signer"
    __table_args__ = (
        UniqueConstraint(
            "document_type", "document_id", "tenant_id",
            name="uq_document_signer_doc_tenant",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    document_type: Mapped[str] = mapped_column(String(50), nullable=False)
    document_id: Mapped[int] = mapped_column(Integer, nullable=False)
    tenant_id: Mapped[int] = mapped_column(ForeignKey("tenant.id"), nullable=False)
