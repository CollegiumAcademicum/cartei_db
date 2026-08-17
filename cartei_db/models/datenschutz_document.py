from cartei_db.base import Base
from cartei_db.models.document_base import DocumentColumns


class DatenschutzDocument(DocumentColumns, Base):
    __tablename__ = "datenschutz_document"
