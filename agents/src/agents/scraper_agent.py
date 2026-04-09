import logging
from typing import Annotated

from autogen_agentchat.agents import AssistantAgent
from autogen_ext.models.openai import OpenAIChatCompletionClient

from agents.config import config
from agents.tools.database import get_db_stats, save_headlines_to_db
from agents.tools.scraper import HeadlineScraper, MAX_SCRAPE_COUNT

logger = logging.getLogger(__name__)


def _validate_max_headlines(value: object) -> str | None:
    """AutoGen agent tool function."""
    if isinstance(value, bool):
        return "Invalid max_headlines: bool is not allowed; provide an integer"
    if not isinstance(value, int):
        return "Invalid max_headlines: must be an integer"
    if value < 1 or value > MAX_SCRAPE_COUNT:
        return (
            "Invalid max_headlines: "
            f"must be between 1 and {MAX_SCRAPE_COUNT}"
        )
    return None


def create_scraper_agent() -> AssistantAgent:
    """Create the web scraper agent."""

    model_client = OpenAIChatCompletionClient(
        model=config.openai_model,
        api_key=config.openai_api_key,
    )

    def scrape_and_save(
        max_headlines: Annotated[
            int,
            "Maximum number of real headlines to scrape and save. "
            f"Must be an integer between 1 and {MAX_SCRAPE_COUNT}.",
        ] = 10,
    ) -> str:
        """Scrape headlines and save to database for AutoGen."""
        validation_error = _validate_max_headlines(max_headlines)
        if validation_error:
            return validation_error
        try:
            logger.info("Scraping up to %s headlines...", max_headlines)

            scraper = HeadlineScraper()
            headlines = scraper.scrape()[:max_headlines]

            if not headlines:
                return "❌ No headlines scraped. Check scraper configuration."

            formatted = [
                {
                    "text": h["text"],
                    "is_real": True,
                    "source_url": h["source_url"],
                }
                for h in headlines
            ]

            result = save_headlines_to_db(formatted)
            stats = get_db_stats()

            return f"✅ Scraping complete!\n\n{result}\n\n{stats}"

        except Exception as e:
            logger.error("Scraper tool failed: %s", e, exc_info=True)
            return f"❌ Scraping failed: {str(e)}"

    agent = AssistantAgent(
        name="scraper_agent",
        model_client=model_client,
        system_message="""You are a web scraping specialist.

When asked to scrape headlines:
1. Call the scrape_and_save tool with the requested count
2. Report the results clearly
3. Do NOT make up data - only use the tool output

Be concise and factual.""",
        description="Scrapes real Florida Man headlines from the web",
        tools=[scrape_and_save, get_db_stats],
    )

    return agent
