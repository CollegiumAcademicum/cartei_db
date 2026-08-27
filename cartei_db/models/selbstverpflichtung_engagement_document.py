from cartei_db.base import Base
from cartei_db.models.document_base import DocumentColumns


class SelbstverpflichtungEngagementDocument(DocumentColumns, Base):
    """Selbstverpflichtung Engagement — a plain single-signature document,
    same shape as datenschutz_document."""

    __tablename__ = "selbstverpflichtung_engagement_document"
