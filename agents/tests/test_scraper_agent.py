import pytest
import requests

from agents.tools.scraper import HeadlineScraper

pytestmark = [pytest.mark.external]


def _internet_available() -> bool:
    try:
        requests.get("https://example.com", timeout=3)
        return True
    except Exception:
        return False


@pytest.mark.skipif(
        not _internet_available(),
        reason="No internet connectivity"
)
def test_scrape_floridaman_live_returns_list():
    scraper = HeadlineScraper(target_url="https://floridaman.com/")
    results = scraper.scrape_floridaman_com()

    assert isinstance(results, list)
    # Live site structure can change; we only assert shape if items exist.
    if results:
        first = results[0]
        assert "text" in first
        assert "source_url" in first
        assert isinstance(first["text"], str)
        assert isinstance(first["source_url"], str)


@pytest.mark.skipif(
        not _internet_available(),
        reason="No internet connectivity"
)
def test_scrape_uses_live_or_fallback():
    scraper = HeadlineScraper(target_url="https://floridaman.com/")
    results = scraper.scrape()

    # scrape() should always return list, fallback when live scrape fails
    assert isinstance(results, list)
    assert len(results) >= 1
