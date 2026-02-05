import sys
import os
import logging
from typing import List, Dict, Any

# Add backend to path (must be before app imports)
sys.path.insert(
    0,
    os.path.abspath(os.path.join(os.path.dirname(__file__), "../../backend"))
)

from app.db.database import SessionLocal  # noqa: E402
from app.services.headline_service import HeadlineService  # noqa: E402

logger = logging.getLogger(__name__)


def save_headlines_to_db(headlines: List[Dict[str, Any]]) -> str:
    """Save scraped headlines to the database"""
    db = SessionLocal()
    service = HeadlineService(db)

    saved = 0
    skipped = 0

    try:
        for headline in headlines:
            try:
                service.add_headline(
                    text=headline["text"],
                    is_real=headline.get("is_real", True),
                    source_url=headline.get("source_url")
                )
                saved += 1
                logger.debug(f"Saved: {headline['text'][:50]}...")
            except ValueError:
                skipped += 1
                logger.debug(f"Skipped duplicate: {headline['text'][:50]}...")

        message = f"💾 Saved {saved} new headlines"
        if skipped > 0:
            message += f", skipped {skipped} duplicates"
        
        return message

    except Exception as e:
        logger.error(f"Database save failed: {e}", exc_info=True)
        return f"❌ Database error: {str(e)}"
    finally:
        db.close()


def get_db_stats() -> str:
    """Get database statistics"""
    db = SessionLocal()
    service = HeadlineService(db)

    try:
        stats = service.get_stats()
        return (
            f"📊 Database Stats:\n"
            f"  Total: {stats['total_headlines']}\n"
            f"  Real: {stats['real_headlines']}\n"
            f"  Fake: {stats['fake_headlines']}"
        )
    except Exception as e:
        logger.error(f"Stats retrieval failed: {e}")
        return f"❌ Could not fetch stats: {str(e)}"
    finally:
        db.close()
