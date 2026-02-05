from autogen_agentchat.agents import AssistantAgent
from autogen_ext.models.openai import OpenAIChatCompletionClient
from agents.tools.scraper import HeadlineScraper
from agents.tools.database import save_headlines_to_db, get_db_stats
from agents.config import config
import logging

logger = logging.getLogger(__name__)


def create_scraper_agent() -> AssistantAgent:
    """Create the web scraper agent"""

    model_client = OpenAIChatCompletionClient(
        model=config.openai_model,
        api_key=config.openai_api_key
    )

    def scrape_and_save(max_headlines: int = 10) -> str:
        """Scrape headlines and save to database - SYNC function for AutoGen"""
        try:
            logger.info(f"🕷️ Scraping up to {max_headlines} headlines...")

            scraper = HeadlineScraper()
            headlines = scraper.scrape()[:max_headlines]

            if not headlines:
                return "❌ No headlines scraped. Check scraper configuration."

            # Format for database
            formatted = [
                {
                    "text": h["text"],
                    "is_real": True,
                    "source_url": h["source_url"]
                }
                for h in headlines
            ]

            # Save to database
            result = save_headlines_to_db(formatted)
            stats = get_db_stats()

            return f"✅ Scraping complete!\n\n{result}\n\n{stats}"

        except Exception as e:
            logger.error(f"Scraper tool failed: {e}", exc_info=True)
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
