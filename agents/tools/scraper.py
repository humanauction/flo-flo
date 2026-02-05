import requests from bs4 import BeautifulSoup
from typing import List, Dict, Optional
import logging

logger = logging.getLogger(__name__)


class HeadlineScraper:
    """ Scrape Florida Man-style headlines from various online sources and news outlets. """

    def __init__(self, target_url: str = "https://floridaman.com/"):
        self.target_url = target_url
        self.headers = {
         "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }

    def scrape_floridaman_com(self) -> List[Dict[str, str]]:
        """ Scrape headlines from floridaman.com, return list of headline dictionaries. """
        try:
            response = requests.get(self.target_url, headers=self.headers, timeout=10)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, 'html.parser')
            headlines = []

            # Find article titles (adjust selectors based on actual site(s) structure)
            articles = soup.find_all("article") or soup.find_all("div", class_="post")

            for article in articles[:10]:  # Limit to 10 per scrape
                title_elem = article.find(["h1", "h2", "h3", "a"])
                link_elem = article.find("a", href=True)

                if title_elem and link_elem:
                    title = title_elem.get_text(strip=True)
                    url = link_elem["href"]
                
                    # Make URL absolute if relative
                    if not url.startswith("http"):
                        url = f"{self.target_url.rstrip('/')}/{url.lstrip('/')}"

                    if title and "florida man" in title.lower():
                        headlines.append({
                            "text": title,
                            "source_url": url
                        })
            
            logger.info(f"Scrapped {len(headlines)} headlines from {self.target_url}")
            return headlines
        
        except Exception as e:
            logger.error(f"Error scraping {self.target_url}: {e}")
            return []
    
    def scrape_fallback(self) -> List[Dict[str, str]]:
        """ Fallback scraping method for other sources if needed. """
        # TODO Implement additional scraping logic for other sources if/as needed
        return [
            {
                "text": "Florida man arrested for throwing alligator through Wendy's drive-thru window",
                "source_url": "https://www.nbcnews.com/news/us-news/florida-man-threw-alligator-through-drive-thru-window-police-say-n856546"
            },
            {
                "text": "Florida man caught on camera licking doorbell for 3 hours",
                "source_url": "https://www.cnn.com/2019/01/07/us/doorbell-licker-california-trnd/index.html"
            },
            {
                "text": "Florida man tries to pay for McDonald's with bag of marijuana",
                "source_url": "https://www.palmbeachpost.com/story/news/crime/2018/03/02/florida-man-tried-to-pay-for-mcdonalds-order-with-weed-cops-say/9875026007/"
            },
        ]

def scrape(self) -> List[Dict[str, str]]:
    """ Main scrape methond, including fallback if primary fails. """
    headlines = self.scrape_floridaman_com()

    if not headlines:
        logger.warning("Primary scrape failed, using fallback headlines")
        headlines = self.scrape_fallback()
    return headlines

def scrape_headlines(max_count: int = 10) -> str:
    """ AutoGen agent tool function to scrape headlines and return formatted string. """
    scraper = HeadlineScraper()
    headlines = scraper.scrape()[:max_count]

    result  = f"Scraped {len(headlines)} headlines:\n\n"
    for i, h in enumerate(headlines, 1):
        result += f"{i}. {h['text']}\n Source: {h['source_url']}\n\n"

    return result
