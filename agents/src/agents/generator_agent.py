import logging

from autogen_agentchat.agents import AssistantAgent
from autogen_ext.models.openai import OpenAIChatCompletionClient

from agents.config import config
from agents.tools.database import get_db_stats, save_headlines_to_db

logger = logging.getLogger(__name__)


def create_generator_agent() -> AssistantAgent:
    """Create the fake headline generator agent."""

    model_client = OpenAIChatCompletionClient(
        model=config.openai_model,
        api_key=config.openai_api_key,
    )

    def generate_fake_headlines(count: int = 5) -> str:
        """Generate fake Florida Man headlines - SYNC function."""
        try:
            logger.info("🤖 Generating %s fake headlines...", count)

            # Hardcoded templates for now (will replace with LLM call)
            templates = [
                (
                    "Florida man attempts to ride shopping cart down I-95 "
                    "during rush hour"
                ),
                (
                    "Florida man arrested for teaching pet iguana to "
                    "shoplift at 7-Eleven"
                ),
                (
                    "Florida man builds treehouse in Walmart parking lot, "
                    "claims squatter's rights"
                ),
                (
                    "Florida man caught using fishing rod to steal donuts "
                    "from bakery window"
                ),
                (
                    "Florida man tries to pay bail with stack of expired "
                    "Taco Bell coupons"
                ),
                (
                    "Florida man starts fire trying to cook eggs with a "
                    "clothes iron"
                ),
                "Florida man arrested for breaking into jail to visit friends",
                "Florida man uses alligator to shotgun a beer at party",
                "Florida man calls 911 to report his stolen drugs",
                "Florida man caught driving stolen golf cart to liquor store",
            ]

            fake_headlines = templates[:count]

            formatted = [
                {"text": headline, "is_real": False, "source_url": None}
                for headline in fake_headlines
            ]

            result = save_headlines_to_db(formatted)

            return (
                f"✅ Generated {len(fake_headlines)} fake headlines\n\n"
                f"{result}"
            )

        except Exception as e:
            logger.error("Generator tool failed: %s", e, exc_info=True)
            return f"❌ Generation failed: {str(e)}"

    agent = AssistantAgent(
        name="generator_agent",
        model_client=model_client,
        system_message="""You are a creative headline generator.

When asked to generate fake headlines:
1. Call the generate_fake_headlines tool with the requested count
2. Report how many were created
3. Do NOT make up data - only use the tool output

Be concise.""",
        description="Generates fake Florida Man headlines",
        tools=[generate_fake_headlines, get_db_stats],
    )

    return agent
