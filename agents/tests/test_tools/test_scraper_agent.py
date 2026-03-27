from agents.tools.scraper import HeadlineScraper, scrape_headlines
from typing import Any, cast


def test_scrape_fallback_returns_expected_shape():
    scraper = HeadlineScraper()
    results = scraper.scrape_fallback()

    assert isinstance(results, list)
    assert len(results) >= 1
    first = results[0]
    assert "text" in first
    assert "source_url" in first
    assert isinstance(first["text"], str)
    assert isinstance(first["source_url"], str)


def test_scrape_headlines_string_output_uses_fallback_without_network(
    monkeypatch,
):
    scraper = HeadlineScraper()

    # Force no network path
    monkeypatch.setattr(scraper, "scrape_floridaman_com", lambda: [])
    monkeypatch.setattr(
        "agents.tools.scraper.HeadlineScraper",
        lambda: scraper
    )

    output = scrape_headlines(max_count=2)

    assert "Scraped 2 headlines" in output
    assert "Source:" in output


def test_scrape_headlines_rejects_bad_max_count():
    assert "Invalid max_count" in scrape_headlines(max_count=0)
    assert "Invalid max_count" in scrape_headlines(max_count=999)
    bad_count = cast(Any, "2")
    assert "must be an integer" in scrape_headlines(max_count=bad_count)


def test_scrape_dedupes_by_normalized_text(monkeypatch):
    scraper = HeadlineScraper()

    monkeypatch.setattr(
        scraper,
        "scrape_floridaman_com",
        lambda: [
            {
                "text": "Florida Man  does  a thing",
                "source_url": "https://example.com/1",
            },
            {
                "text": "  florida man does a thing ",
                "source_url": "https://example.com/2",
            },
        ],
    )

    results = scraper.scrape()
    assert len(results) == 1
    assert results[0]["text"] == "Florida Man does a thing"
