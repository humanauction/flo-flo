from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional, List
from app.models.headline import Headline


class HeadlineRepository:
    """Database operations for headlines"""

    def __init__(self, db: Session):
        self.db = db

    def create(self, text: str, is_real: bool, source_url: Optional[str] = None) -> Headline:
        """Create a new headline"""
        headline = Headline(
            text=text,
            is_real=is_real,
            source_url=source_url
        )
        self.db.add(headline)
        self.db.commit()
        self.db.refresh(headline)
        return headline

    def get_by_id(self, headline_id: int) -> Optional[Headline]:
        """Get headline by ID"""
        return self.db.query(Headline).filter(Headline.id == headline_id).first()

    def get_random(self) -> Optional[Headline]:
        """Get a random headline for the game"""
        return self.db.query(Headline).order_by(func.random()).first()

    def get_all(self, skip: int = 0, limit: int = 100) -> List[Headline]:
        """Get all headlines with pagination"""
        return self.db.query(Headline).offset(skip).limit(limit).all()

    def count_total(self) -> int:
        """Count total headlines"""
        return self.db.query(Headline).count()

    def count_real(self) -> int:
        """Count real headlines"""
        return self.db.query(Headline).filter(Headline.is_real.is_(True)).count()  # ← SQLAlchemy syntax for queries

    def count_fake(self) -> int:
        """Count fake headlines"""
        return self.db.query(Headline).filter(Headline.is_real.is_(False)).count()  # ← SQLAlchemy syntax for queries

    def exists(self, text: str) -> bool:
        """Check if headline already exists"""
        return self.db.query(Headline).filter(Headline.text == text).first() is not None

    def delete(self, headline_id: int) -> bool:
        """Delete a headline by ID"""
        headline = self.get_by_id(headline_id)
        if headline:
            self.db.delete(headline)
            self.db.commit()
            return True
        return False
