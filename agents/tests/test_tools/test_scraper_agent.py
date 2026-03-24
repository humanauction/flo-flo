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


def test_scrape_headlines_string_output_uses_fallback_without_network(monkeypatch):
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
