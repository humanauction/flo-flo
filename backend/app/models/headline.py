from datetime import datetime
from sqlalchemy import String, Boolean, DateTime, Text, func
from sqlalchemy.orm import Mapped, mapped_column
from app.db.database import Base


class Headline(Base):
    """Florida Man headline - real or generated"""

    __tablename__ = "headlines"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    text: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    # True = real, False = AI
    is_real: Mapped[bool] = mapped_column(Boolean, nullable=False)
    # Only real headlines
    source_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    scraped_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    embedding: Mapped[bytes | None] = mapped_column(
        nullable=True
    )  # Store as bytes; convert to vector in app logic
    embedding_model: Mapped[str | None] = mapped_column(String(64), nullable=True)
    embedded_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    def __repr__(self):
        return (
            f"<Headline(id={self.id}, is_real={self.is_real}, "
            f"text='{self.text[:50]}...')>"
        )
