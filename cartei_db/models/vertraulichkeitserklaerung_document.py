from cartei_db.base import Base
from cartei_db.models.document_base import DocumentColumns


class VertraulichkeitserklaerungDocument(DocumentColumns, Base):
    __tablename__ = "vertraulichkeitserklaerung_document"
