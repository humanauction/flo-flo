from autogen_agentchat.agents import AssistantAgent
from autogen_ext.models.openai import OpenAIChatCompletionClient
from agents.tools.scraper import HeadlineScraper
from agents.tools.database import save_headlines_to_db, get_db_stats
from agents.config import config


def create_scraper_agent() -> AssistantAgent:
    """Scraper agent"""

    model_client = OpenAIChatCompletionClient(
        model=config.openai_model,
        api_key=config.openai_api_key
    )

    async def scrape_and_save(max_headlines: int = 10) -> str:
        """Scrape headlines and save to database"""
        scraper = HeadlineScraper()
        headlines = scraper.scrape()[:max_headlines]

        # Format for database
        formatted = [
            {"text": h["text"], "is_real": True, "source_url": h["source_url"]}
            for h in headlines
        ]

        # Save to database
        result = save_headlines_to_db(formatted)
        stats = get_db_stats()

        return f"{result}\n\n{stats}"

    agent = AssistantAgent(
        name="scraper_agent",
        model_client=model_client,
        system_message="""You are a web scraping specialist focused on collecting real Florida Man headlines.

Your job:
1. Scrape headlines from floridaman.com and other sources
2. Extract the headline text and source URL
3. Save valid headlines to the database
4. Report statistics

Only collect headlines that are genuinely bizarre Florida Man stories.""",
        description="Scrapes real Florida Man headlines from the web",
        tools=[scrape_and_save, get_db_stats],
    )

    return agent
