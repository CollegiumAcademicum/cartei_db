from cartei_db.base import Base
from cartei_db.models.document_base import DocumentColumns


class PhotoerlaubnisDocument(DocumentColumns, Base):
    __tablename__ = "photoerlaubnis_document"
