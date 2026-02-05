import asyncio
import logging
from autogen_agentchat.teams import RoundRobinGroupChat
from autogen_agentchat.conditions import TextMentionTermination
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

    # Create termination condition
    termination = TextMentionTermination("TERMINATE")

    # Create team with round-robin chat
    team = RoundRobinGroupChat(
        [scraper, generator],
        termination_condition=termination
    )

    # Run the pipeline
    task = (
        f"Collect {scrape_count} real Florida Man headlines "
        f"and generate {generate_count} fake headlines.\n\n"
        "Steps:\n"
        "1. Scrape real headlines\n"
        "2. Generate fake headlines\n"
        "3. Show final database stats\n"
        "4. Reply with TERMINATE when done"
    )

    logger.info(f"📋 Task: {task}")

    try:
        result = await team.run(task=task)
        logger.info("✅ Pipeline complete!")
        return result
    except Exception as e:
        logger.error(f"❌ Pipeline failed: {e}")
        raise


async def main():
    """Main entry point"""
    await run_headline_pipeline(scrape_count=5, generate_count=5)


if __name__ == "__main__":
    asyncio.run(main())
