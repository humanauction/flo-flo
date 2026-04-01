import logging
import time
from typing import Callable, Dict, List, TypedDict, cast

import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

MAX_SCRAPE_COUNT = 50
DEFAULT_TIMEOUT_SECONDS = 10
DEFAULT_MAX_RETRIES = 3
DEFAULT_BACKOFF_BASE_SECONDS = 0.5
SOURCE_FLORIDAMAN_PRIMARY = "floridaman_primary"
SOURCE_FALLBACK_STATIC = "fallback_static"


class SourceMetrics(TypedDict):
    fetched: int
    kept: int
    invalid: int
    duplicates: int


class ScrapeMetrics(TypedDict):
    fetched_total: int
    kept_total: int
    invalid_dropped: int
    duplicates_dropped: int
    by_source: Dict[str, SourceMetrics]


class ScrapeResult(TypedDict):
    headlines: List[Dict[str, str]]
    metrics: ScrapeMetrics


class HeadlineScraper:
    """
    Scrape Florida Man-style headlines from various
    online sources and news outlets.
    """

    def __init__(
        self,
        target_url: str = "https://floridaman.com/",
        timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS,
        max_retries: int = DEFAULT_MAX_RETRIES,
        backoff_base_seconds: float = DEFAULT_BACKOFF_BASE_SECONDS,
        enabled_sources: tuple[str, ...] = (
            SOURCE_FLORIDAMAN_PRIMARY,
            SOURCE_FALLBACK_STATIC,
        ),
        source_max_items: int = 10,
        min_headline_chars: int = 12,
        require_florida_keyword: bool = True,
    ):
        if not isinstance(target_url, str) or not target_url.strip():
            raise ValueError("target_url must be a non-empty string")
        if not target_url.startswith(("http://", "https://")):
            raise ValueError("target_url must start with http:// or https://")
        if not isinstance(timeout_seconds, int) or timeout_seconds < 1:
            raise ValueError("timeout_seconds must be a positive integer")
        if not isinstance(max_retries, int) or max_retries < 1:
            raise ValueError("max_retries must be a positive integer")
        if (
            not isinstance(backoff_base_seconds, (int, float))
            or backoff_base_seconds <= 0
        ):
            raise ValueError("backoff_base_seconds must be a positive number")
        if not enabled_sources:
            raise ValueError(
                "enabled_sources must contain at least one source"
            )
        if not isinstance(source_max_items, int) or source_max_items < 1:
            raise ValueError("source_max_items must be a positive integer")
        if not isinstance(min_headline_chars, int) or min_headline_chars < 1:
            raise ValueError("min_headline_chars must be a positive integer")
        if not isinstance(require_florida_keyword, bool):
            raise ValueError("require_florida_keyword must be a boolean")

        self.target_url = target_url
        self.timeout_seconds = timeout_seconds
        self.max_retries = max_retries
        self.backoff_base_seconds = float(backoff_base_seconds)
        self.enabled_sources = enabled_sources
        self.source_max_items = source_max_items
        self.min_headline_chars = min_headline_chars
        self.require_florida_keyword = require_florida_keyword
        self.headers = {
            "User-Agent": (
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36"
            )
        }
        # Store method names (not bound methods) so monkeypatching works.
        self._source_adapters: dict[str, str] = {
            SOURCE_FLORIDAMAN_PRIMARY: "scrape_floridaman_com",
            SOURCE_FALLBACK_STATIC: "scrape_fallback",
        }

    def _fetch_with_retries(self) -> requests.Response | None:
        for attempt in range(1, self.max_retries + 1):
            try:
                response = requests.get(
                    self.target_url,
                    headers=self.headers,
                    timeout=self.timeout_seconds,
                )
                response.raise_for_status()
                return response
            except requests.RequestException as exc:
                if attempt >= self.max_retries:
                    logger.error(
                        "Scrape failed after %s attempts for %s: %s",
                        self.max_retries,
                        self.target_url,
                        exc,
                    )
                    return None

                backoff = self.backoff_base_seconds * (2 ** (attempt - 1))
                logger.warning(
                    (
                        "Scrape attempt %s/%s failed for %s: %s. "
                        "Retrying in %.2fs"
                    ),
                    attempt,
                    self.max_retries,
                    self.target_url,
                    exc,
                    backoff,
                )
                time.sleep(backoff)

        return None

    @staticmethod
    def _normalize_text(value: str) -> str:
        return " ".join(value.split()).strip()

    @staticmethod
    def _empty_source_metrics() -> SourceMetrics:
        return {"fetched": 0, "kept": 0, "invalid": 0, "duplicates": 0}

    def _empty_metrics(self) -> ScrapeMetrics:
        return {
            "fetched_total": 0,
            "kept_total": 0,
            "invalid_dropped": 0,
            "duplicates_dropped": 0,
            "by_source": {
                source_id: self._empty_source_metrics()
                for source_id in self.enabled_sources
            },
        }

    def _sanitize_headline(
        self,
        headline: Dict[str, str],
    ) -> Dict[str, str] | None:
        text = headline.get("text")
        source_url = headline.get("source_url")

        if not isinstance(text, str) or not text.strip():
            return None
        if not isinstance(source_url, str) or not source_url.strip():
            return None

        text_clean = self._normalize_text(text)
        if len(text_clean) < self.min_headline_chars:
            return None
        if (
            self.require_florida_keyword
            and "florida man" not in text_clean.lower()
        ):
            return None

        return {
            "text": text_clean,
            "source_url": source_url.strip(),
        }

    def _collect_source(
        self,
        source_id: str,
        raw_headlines: List[Dict[str, str]],
        seen: set[str],
        metrics: ScrapeMetrics,
    ) -> List[Dict[str, str]]:
        source_metrics = metrics["by_source"].setdefault(
            source_id,
            self._empty_source_metrics(),
        )
        source_metrics["fetched"] += len(raw_headlines)
        metrics["fetched_total"] += len(raw_headlines)

        kept: List[Dict[str, str]] = []
        for item in raw_headlines:
            cleaned = self._sanitize_headline(item)
            if cleaned is None:
                source_metrics["invalid"] += 1
                metrics["invalid_dropped"] += 1
                continue

            normalized = cleaned["text"].lower()
            if normalized in seen:
                source_metrics["duplicates"] += 1
                metrics["duplicates_dropped"] += 1
                continue

            seen.add(normalized)
            source_metrics["kept"] += 1
            metrics["kept_total"] += 1
            kept.append(cleaned)

        return kept

    def scrape_floridaman_com(self) -> List[Dict[str, str]]:
        """Scrape headlines from floridaman.com."""
        try:
            response = self._fetch_with_retries()
            if response is None:
                return []

            soup = BeautifulSoup(response.text, "html.parser")
            headlines: List[Dict[str, str]] = []

            articles = soup.find_all("article")
            if not articles:
                articles = soup.find_all("div", class_="post")

            for article in articles[: self.source_max_items]:
                title_elem = article.find(["h1", "h2", "h3", "a"])
                link_elem = article.find("a", href=True)

                if title_elem and link_elem:
                    title = title_elem.get_text(strip=True)
                    url = link_elem.get("href", "")

                    if isinstance(url, str) and not url.startswith("http"):
                        url = (
                            f"{self.target_url.rstrip('/')}/"
                            f"{url.lstrip('/')}"
                        )

                    if title and "florida man" in title.lower():
                        headlines.append({"text": title, "source_url": url})

            logger.info(
                "Scraped %s headlines from %s",
                len(headlines),
                self.target_url,
            )
            return headlines

        except Exception as e:
            logger.error("Error scraping %s: %s", self.target_url, e)
            return []

    def scrape_fallback(self) -> List[Dict[str, str]]:
        """Fallback headlines if scraping fails."""
        return [
            {
                "text": (
                    "Florida man arrested for throwing alligator through "
                    "Wendy's drive-thru window"
                ),
                "source_url": (
                    "https://www.nbcnews.com/news/us-news/"
                    "florida-man-threw-alligator-through-drive-thru-window-"
                    "police-say-n856546"
                ),
            },
            {
                "text": (
                    "Florida man caught on camera licking doorbell "
                    "for 3 hours"
                ),
                "source_url": (
                    "https://www.cnn.com/2019/01/07/us/"
                    "doorbell-licker-california-trnd/index.html"
                ),
            },
            {
                "text": (
                    "Florida man tries to pay for McDonald's with bag "
                    "of marijuana"
                ),
                "source_url": (
                    "https://www.palmbeachpost.com/story/news/crime/2018/03/"
                    "02/florida-man-tried-to-pay-for-mcdonalds-order-with-"
                    "weed-cops-say/9875026007/"
                ),
            },
        ]

    def scrape_with_metrics(self) -> ScrapeResult:
        """Scrape headlines from configured sources with metrics."""
        metrics = self._empty_metrics()
        seen: set[str] = set()
        merged: List[Dict[str, str]] = []

        for source_id in self.enabled_sources:
            if (
                source_id == SOURCE_FALLBACK_STATIC
                and metrics["kept_total"] > 0
            ):
                # Conservative strategy: fallback only if primary == 0 kept.
                continue

            adapter_name = self._source_adapters.get(source_id)
            if adapter_name is None:
                continue

            adapter_obj = getattr(self, adapter_name, None)
            if adapter_obj is None or not callable(adapter_obj):
                continue

            adapter = cast(
                Callable[[], List[Dict[str, str]]],
                adapter_obj,
            )
            raw = adapter()
            kept = self._collect_source(source_id, raw, seen, metrics)
            merged.extend(kept)

        return {"headlines": merged, "metrics": metrics}

    def scrape(self) -> List[Dict[str, str]]:
        """Backwards-compatible list-only API."""
        return self.scrape_with_metrics()["headlines"]


def scrape_headlines(max_count: int = 10) -> str:
    """AutoGen agent tool function."""
    if not isinstance(max_count, int):
        return "Invalid max_count: must be an integer"
    if max_count < 1 or max_count > MAX_SCRAPE_COUNT:
        return f"Invalid max_count: must be between 1 and {MAX_SCRAPE_COUNT}"

    scraper = HeadlineScraper()
    scrape_result = scraper.scrape_with_metrics()
    headlines = scrape_result["headlines"][:max_count]
    metrics = scrape_result["metrics"]

    result = f"Scraped {len(headlines)} headlines:\n\n"
    for i, h in enumerate(headlines, 1):
        text = h.get("text", "(missing text)")
        source = h.get("source_url", "(missing source)")
        result += f"{i}. {text}\n   Source: {source}\n\n"

    result += (
        "Metrics:\n"
        f"- fetched_total={metrics['fetched_total']}\n"
        f"- kept_total={metrics['kept_total']}\n"
        f"- invalid_dropped={metrics['invalid_dropped']}\n"
        f"- duplicates_dropped={metrics['duplicates_dropped']}\n"
    )
    for source_id, source_metrics in metrics["by_source"].items():
        result += (
            f"- {source_id}: "
            f"fetched={source_metrics['fetched']}, "
            f"kept={source_metrics['kept']}, "
            f"invalid={source_metrics['invalid']}, "
            f"duplicates={source_metrics['duplicates']}\n"
        )

    return result
