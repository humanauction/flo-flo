from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text
from sqlalchemy.sql import func
from app.db.database import Base


class Headline(Base):
    """Florida Man headline - real or generated"""

    __tablename__ = "headlines"

    id = Column(Integer, primary_key=True, index=True)
    text = Column(Text, nullable=False, unique=True)
    is_real = Column(Boolean, nullable=False)  # True = real, False = AI
    source_url = Column(String(500), nullable=True)  # Only for real headlines
    scraped_at = Column(DateTime(timezone=True), server_default=func.now())
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    def __repr__(self):
        return (
            f"<Headline(id={self.id}, is_real={self.is_real}, "
            f"text='{self.text[:50]}...')>"
        )
