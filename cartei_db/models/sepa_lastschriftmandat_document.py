from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from cartei_db.base import Base
from cartei_db.models.document_base import DocumentColumns


class SepaLastschriftmandatDocument(DocumentColumns, Base):
    """SEPA-Lastschriftmandat: the signed direct-debit mandate plus its
    structured fields, entered on upload. signed_at (from DocumentColumns) is
    the mandate signing date."""

    __tablename__ = "sepa_lastschriftmandat_document"

    mandatsreferenz: Mapped[str] = mapped_column(String, nullable=False)
    kontoinhaber: Mapped[str] = mapped_column(String, nullable=False)
    bank_name: Mapped[str] = mapped_column(String, nullable=False)
    iban: Mapped[str] = mapped_column(String, nullable=False)
    bic: Mapped[str] = mapped_column(String, nullable=False)