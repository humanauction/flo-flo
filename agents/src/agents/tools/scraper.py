import logging
import time
from typing import Dict, List

import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

MAX_SCRAPE_COUNT = 50
DEFAULT_TIMEOUT_SECONDS = 10
DEFAULT_MAX_RETRIES = 3
DEFAULT_BACKOFF_BASE_SECONDS = 0.5


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

        self.target_url = target_url
        self.timeout_seconds = timeout_seconds
        self.max_retries = max_retries
        self.backoff_base_seconds = float(backoff_base_seconds)
        self.headers = {
            "User-Agent": (
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36"
            )
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

    def _dedupe_headlines(
        self,
        headlines: List[Dict[str, str]],
    ) -> List[Dict[str, str]]:
        seen: set[str] = set()
        deduped: List[Dict[str, str]] = []

        for headline in headlines:
            text = headline.get("text")
            source_url = headline.get("source_url")

            if not isinstance(text, str) or not text.strip():
                continue
            if not isinstance(source_url, str) or not source_url.strip():
                continue

            normalized = self._normalize_text(text).lower()
            if normalized in seen:
                continue

            seen.add(normalized)
            deduped.append(
                {
                    "text": self._normalize_text(text),
                    "source_url": source_url.strip(),
                }
            )

        return deduped

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

            for article in articles[:10]:
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

            headlines = self._dedupe_headlines(headlines)

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

    def scrape(self) -> List[Dict[str, str]]:
        """Main scrape method with fallback."""
        headlines = self.scrape_floridaman_com()

        if not headlines:
            logger.warning("Primary scrape failed, using fallback headlines")
            headlines = self.scrape_fallback()

        return self._dedupe_headlines(headlines)


def scrape_headlines(max_count: int = 10) -> str:
    """AutoGen agent tool function."""
    if not isinstance(max_count, int):
        return "Invalid max_count: must be an integer"
    if max_count < 1 or max_count > MAX_SCRAPE_COUNT:
        return f"Invalid max_count: must be between 1 and {MAX_SCRAPE_COUNT}"

    scraper = HeadlineScraper()
    headlines = scraper.scrape()[:max_count]

    result = f"Scraped {len(headlines)} headlines:\n\n"
    for i, h in enumerate(headlines, 1):
        text = h.get("text", "(missing text)")
        source = h.get("source_url", "(missing source)")
        result += f"{i}. {text}\n   Source: {source}\n\n"

    return result
