from __future__ import annotations
import datetime
from typing import Optional
from sqlalchemy import String, DateTime, func, Text
from sqlalchemy.orm import Mapped, mapped_column
from app.db.database import Base
from pgvector.sqlalchemy import Vector
from app.config import settings


class Headline(Base):
    __tablename__ = "headlines"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    headline: Mapped[str] = mapped_column(String, unique=True, index=True)
    source: Mapped[str] = mapped_column(String)
    is_real: Mapped[bool] = mapped_column()
    scraped_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    article_text: Mapped[Optional[str]] = mapped_column(Text)
    article_url: Mapped[Optional[str]] = mapped_column(String)

    # Corrected type hint and added Vector type
    embedding: Mapped[Optional[list[float]]] = mapped_column(
        Vector(settings.embedding_dim), nullable=True
    )

    def __repr__(self):
        return (
            f"<Headline(id={self.id}, headline='{self.headline[:30]}...', "
            f"is_real={self.is_real})>"
        )
