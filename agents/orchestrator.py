import asyncio
import logging
from autogen_agentchat.teams import RoundRobinGroupChat
from autogen_agentchat.conditions import MaxMessageTermination
from agents.scraper_agent import create_scraper_agent
from agents.generator_agent import create_generator_agent

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def run_headline_pipeline(
    scrape_count: int = 10,
    generate_count: int = 10
):
    """Run the full headline collection pipeline"""

    logger.info("🚀 Starting AutoGen headline pipeline...")

    # Create agents
    scraper = create_scraper_agent()
    generator = create_generator_agent()

    # Termination: stop after max messages
    termination = MaxMessageTermination(max_messages=10)

    # Create team
    team = RoundRobinGroupChat(
        [scraper, generator],
        termination_condition=termination
    )

    # Simpler task without TERMINATE keyword
    task = (
        f"1. Scraper: collect {scrape_count} real headlines and save to database\n"
        f"2. Generator: create {generate_count} fake headlines and save to database\n"
        f"3. Report final database statistics"
    )

    logger.info(f"📋 Task: {task}")

    try:
        result = await team.run(task=task)
        logger.info("✅ Pipeline complete!")
        logger.info(f"Result: {result}")
        return result
    except Exception as e:
        logger.error(f"❌ Pipeline failed: {e}", exc_info=True)
        raise


async def main():
    """Main entry point"""
    await run_headline_pipeline(scrape_count=5, generate_count=5)


if __name__ == "__main__":
    asyncio.run(main())
