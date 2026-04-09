from typing import Any, cast

import requests

from agents.tools.scraper import HeadlineScraper, scrape_headlines


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

    monkeypatch.setattr(scraper, "scrape_floridaman_com", lambda: [])
    monkeypatch.setattr(
        "agents.tools.scraper.HeadlineScraper",
        lambda: scraper,
    )

    output = scrape_headlines(max_count=2)

    assert "Scraped 2 headlines" in output
    assert "Source:" in output


def test_scrape_headlines_rejects_bad_max_count():
    assert "Invalid max_count" in scrape_headlines(max_count=0)
    assert "Invalid max_count" in scrape_headlines(max_count=999)
    bad_count = cast(Any, "2")
    assert "must be an integer" in scrape_headlines(max_count=bad_count)
    assert "bool is not allowed" in scrape_headlines(max_count=True)


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


def test_scrape_retries_then_succeeds(monkeypatch):
    class FakeResponse:
        text = (
            "<article><h2>Florida Man does a test</h2>"
            "<a href='https://example.com/a'>read</a></article>"
        )

        @staticmethod
        def raise_for_status():
            return None

    attempts = {"count": 0}
    sleeps: list[float] = []

    def fake_get(*args, **kwargs):
        attempts["count"] += 1
        if attempts["count"] == 1:
            raise requests.Timeout("timeout")
        return FakeResponse()

    monkeypatch.setattr("agents.tools.scraper.requests.get", fake_get)
    monkeypatch.setattr("agents.tools.scraper.time.sleep", sleeps.append)

    scraper = HeadlineScraper(max_retries=3, backoff_base_seconds=0.1)
    results = scraper.scrape_floridaman_com()

    assert len(results) == 1
    assert attempts["count"] == 2
    assert len(sleeps) == 1


def test_scrape_with_metrics_tracks_source_counts(monkeypatch):
    scraper = HeadlineScraper()

    monkeypatch.setattr(
        scraper,
        "scrape_floridaman_com",
        lambda: [
            {
                "text": "Florida Man does one thing",
                "source_url": "https://example.com/thing",
            },
            {
                "text": "Florida Man does one thing",
                "source_url": "https://example.com/duplicate",
            },
            {
                "text": "invalid",
                "source_url": "",
            },
        ],
    )
    monkeypatch.setattr(scraper, "scrape_fallback", lambda: [])

    result = scraper.scrape_with_metrics()
    headlines = result["headlines"]
    metrics = result["metrics"]

    assert len(headlines) == 1
    assert headlines[0]["text"] == "Florida Man does one thing"
    assert metrics["fetched_total"] == 3
    assert metrics["kept_total"] == 1
    assert metrics["invalid_dropped"] == 1
    assert metrics["duplicates_dropped"] == 1
    assert metrics["by_source"]["floridaman_primary"]["fetched"] == 3
    assert metrics["by_source"]["floridaman_primary"]["kept"] == 1
    assert metrics["by_source"]["fallback_static"]["fetched"] == 0


def test_scrape_with_metrics_uses_fallback_when_primary_empty(monkeypatch):
    scraper = HeadlineScraper()
    monkeypatch.setattr(scraper, "scrape_floridaman_com", lambda: [])

    result = scraper.scrape_with_metrics()
    metrics = result["metrics"]

    assert len(result["headlines"]) >= 1
    assert metrics["by_source"]["floridaman_primary"]["fetched"] == 0
    assert metrics["by_source"]["fallback_static"]["fetched"] >= 1


def test_scrape_returns_empty_after_retry_exhaustion(monkeypatch):
    sleeps: list[float] = []

    def always_fail(*args, **kwargs):
        raise requests.RequestException("network down")

    monkeypatch.setattr("agents.tools.scraper.requests.get", always_fail)
    monkeypatch.setattr("agents.tools.scraper.time.sleep", sleeps.append)

    scraper = HeadlineScraper(max_retries=3, backoff_base_seconds=0.1)
    results = scraper.scrape_floridaman_com()

    assert results == []
    assert len(sleeps) == 2


def test_scrape_headlines_includes_metrics_summary(monkeypatch):
    scraper = HeadlineScraper()

    monkeypatch.setattr(scraper, "scrape_floridaman_com", lambda: [])
    monkeypatch.setattr(
        "agents.tools.scraper.HeadlineScraper",
        lambda: scraper,
    )
    monkeypatch.setattr(
        scraper,
        "scrape_fallback",
        lambda: [
            {
                "text": "Florida Man does one thing",
                "source_url": "https://example.com/thing",
            }
        ],
    )

    output = scrape_headlines(max_count=1)

    assert "Metrics:" in output
    assert "fetched_total=" in output
    assert "floridaman_primary:" in output
    assert "fallback_static:" in output
