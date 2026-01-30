from sqlalchemy.orm import Session
from app.db.repositories import HeadlineRepository
from app.models.headline import Headline
from typing import Optional, Dict


class HeadlineService:
    """Business logic for headline operations"""

    def __init__(self, db: Session):
        self.repo = HeadlineRepository(db)

    def get_game_headline(self) -> Optional[Dict]:
        """Get a random headline for gameplay (hides answer)"""
        headline = self.repo.get_random()
        if not headline:
            return None

        return {
            "id": headline.id,
            "text": headline.text,
            # Don't expose is_real or source_url until user guesses
        }

    def check_guess(self, headline_id: int, guess: bool) -> Optional[Dict]:
        """Check if user's guess is correct"""
        headline = self.repo.get_by_id(headline_id)
        if not headline:
            return None

        correct = (guess == headline.is_real)

        return {
            "correct": correct,
            "was_real": headline.is_real,
            "source_url": headline.source_url if headline.is_real.is_(True) else None,
            "headline_text": headline.text
        }

    def get_stats(self) -> Dict:
        """Get database statistics"""
        return {
            "total_headlines": self.repo.count_total(),
            "real_headlines": self.repo.count_real(),
            "fake_headlines": self.repo.count_fake()
        }

    def add_headline(self, text: str, is_real: bool, source_url: Optional[str] = None) -> Headline:
        """Add a new headline (from scraper or generator)"""
        if self.repo.exists(text):
            raise ValueError("Headline already exists")

        return self.repo.create(text=text, is_real=is_real, source_url=source_url)
