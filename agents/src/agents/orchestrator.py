import asyncio
import logging
import os
import sys

from autogen_agentchat.conditions import MaxMessageTermination
from autogen_agentchat.teams import RoundRobinGroupChat

from agents.config import config
from agents.generator_agent import create_generator_agent
from agents.scraper_agent import create_scraper_agent

# Keep orchestrator importable when backend isn't installed as a package.
sys.path.insert(
    0,
    os.path.abspath(
        os.path.join(os.path.dirname(__file__), "../../../backend")
    ),
)

from app.db.database import get_db  # noqa: E402
from app.db.repositories import TokenUsageRepository  # noqa: E402

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def run_headline_pipeline(
    scrape_count: int = 10,
    generate_count: int = 10,
):
    """Run the full headline collection pipeline."""

    logger.info("🚀 Starting AutoGen headline pipeline...")

    scraper = create_scraper_agent()
    generator = create_generator_agent()

    termination = MaxMessageTermination(max_messages=10)

    team = RoundRobinGroupChat(
        [scraper, generator],
        termination_condition=termination,
    )

    task = (
        f"1. Scraper: collect {scrape_count} real headlines and save "
        f"to database\n"
        f"2. Generator: create {generate_count} fake headlines and "
        f"save to database\n"
        f"3. Report final database statistics"
    )

    logger.info("📋 Task: %s", task)

    try:
        result = await team.run(task=task)
        logger.info("✅ Pipeline complete!")

        if config.track_tokens and hasattr(result, "messages"):
            db = next(get_db())
            token_repo = TokenUsageRepository(db)

            for msg in result.messages:
                if hasattr(msg, "models_usage") and msg.models_usage:
                    usage = msg.models_usage
                    token_repo.create(
                        agent_name=msg.source,
                        model=config.openai_model,
                        prompt_tokens=getattr(usage, "prompt_tokens", 0),
                        completion_tokens=getattr(
                            usage,
                            "completion_tokens",
                            0,
                        ),
                        total_tokens=getattr(usage, "total_tokens", 0),
                    )
                    logger.info("💰 Logged token usage for %s", msg.source)

            stats = token_repo.get_stats()
            logger.info("📊 Token usage stats: %s", stats)

        return result
    except Exception as e:
        logger.error("❌ Pipeline failed: %s", e, exc_info=True)
        raise


async def main():
    """Main entry point."""
    await run_headline_pipeline(scrape_count=5, generate_count=5)


if __name__ == "__main__":
    asyncio.run(main())
