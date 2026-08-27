from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from cartei_db.base import Base
from cartei_db.models.document_base import DocumentColumns


class BescheidAusbildungsstelleDocument(DocumentColumns, Base):
    """Bescheid für Ausbildungsstellen. signed_at (from DocumentColumns) plus
    the CA-side signer (signed_by_id) — who signed the Bescheid, not the tenant."""

    __tablename__ = "bescheid_ausbildungsstelle_document"

    signed_by_id: Mapped[int] = mapped_column(ForeignKey("tenant.id"), nullable=False)
