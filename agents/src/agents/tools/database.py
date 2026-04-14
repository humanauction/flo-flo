import logging
import os
import sys
from typing import Any

# Ensure backend app package is importable when running only the agents env.
sys.path.insert(
    0,
    os.path.abspath(
        os.path.join(os.path.dirname(__file__), "../../../../backend")
    ),
)

from app.db.database import SessionLocal  # noqa: E402
from app.services.headline_service import HeadlineService  # noqa: E402

logger = logging.getLogger(__name__)

MAX_HEADLINE_BATCH = 100
MAX_CONTEXT_LIMIT = 10
DEFAULT_CONTEXT_LIMIT = 3


def _normalize_headline_payload(item: Any) -> dict[str, Any] | None:
    if not isinstance(item, dict):
        return None

    text = item.get("text")
    if not isinstance(text, str) or not text.strip():
        return None

    is_real = item.get("is_real", True)
    if not isinstance(is_real, bool):
        return None

    source_url = item.get("source_url")
    if source_url is not None and not isinstance(source_url, str):
        return None

    return {
        "text": " ".join(text.split()).strip(),
        "is_real": is_real,
        "source_url": source_url,
    }


def save_headlines_to_db(headlines: list[dict[str, Any]]) -> str:
    """Save scraped headlines to the database."""
    if not isinstance(headlines, list):
        return "Invalid payload: headlines must be a list"
    if len(headlines) > MAX_HEADLINE_BATCH:
        return f"Invalid payload: max {MAX_HEADLINE_BATCH} headlines per batch"

    db = SessionLocal()
    service = HeadlineService(db)

    saved = 0
    skipped = 0
    invalid = 0

    try:
        for headline in headlines:
            normalized = _normalize_headline_payload(headline)
            if normalized is None:
                invalid += 1
                continue

            try:
                service.add_headline(
                    text=normalized["text"],
                    is_real=normalized["is_real"],
                    source_url=normalized["source_url"],
                )
                saved += 1
                logger.debug("Saved: %s...", normalized["text"][:50])
            except ValueError:
                skipped += 1
                logger.debug(
                    "Skipped duplicate: %s...",
                    normalized["text"][:50],
                )

        message = f"Saved {saved} new headlines"
        if skipped > 0:
            message += f", skipped {skipped} duplicates"
        if invalid > 0:
            message += f", invalid {invalid} entries"

        return message

    except Exception as e:
        logger.error("Database save failed: %s", e, exc_info=True)
        return f"Database error: {str(e)}"
    finally:
        db.close()


def get_db_stats() -> str:
    """Get database statistics."""
    db = SessionLocal()
    service = HeadlineService(db)

    try:
        stats = service.get_stats()
        return (
            f"Database Stats:\n"
            f"  Total: {stats['total_headlines']}\n"
            f"  Real: {stats['real_headlines']}\n"
            f"  Fake: {stats['fake_headlines']}"
        )
    except Exception as e:
        logger.error("Stats retrieval failed: %s", e)
        return f"❌ Could not fetch stats: {str(e)}"
    finally:
        db.close()


def _normalize_context_limit(limit: Any) -> int:
    if isinstance(limit, bool) or not isinstance(limit, int):
        return DEFAULT_CONTEXT_LIMIT
    return max(1, min(limit, MAX_CONTEXT_LIMIT))


def get_recent_real_headline_context(
        limit: int = DEFAULT_CONTEXT_LIMIT
) -> list[dict[str, Any]]:
    """Fetch recent real headlines for RAG context."""
    db = SessionLocal()
    service = HeadlineService(db)

    safe_limit = _normalize_context_limit(limit)

    try:
        return service.get_recent_real_headline_context(limit=safe_limit)
    except Exception as e:
        logger.error("Context retrieval failed: %s", e, exc_info=True)
        return []
    finally:
        db.close()
