from cartei_db.base import Base
from cartei_db.models.document_base import DocumentColumns


class MietbedingungenDocument(DocumentColumns, Base):
    __tablename__ = "mietbedingungen_document"
