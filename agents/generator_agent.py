from autogen_agentchat.agents import AssistantAgent
from autogen_ext.models.openai import OpenAIChatCompletionClient
from agents.tools.database import save_headlines_to_db, get_db_stats
from agents.config import config


def create_generator_agent() -> AssistantAgent:
    """Create the fake headline generator agent"""

    model_client = OpenAIChatCompletionClient(
        model=config.openai_model,
        api_key=config.openai_api_key
    )

    async def generate_fake_headlines(count: int = 5) -> str:
        """Generate fake Florida Man headlines"""

        # TODO: Call LLM to generate headlines
        # For now, using templates
        fake_headlines = [
            "Florida man attempts to ride shopping cart down I-95 during rush hour",
            "Florida man arrested for teaching pet iguana to shoplift at 7-Eleven",
            "Florida man builds treehouse in Walmart parking lot, claims squatter's rights",
            "Florida man caught using fishing rod to steal donuts from bakery window",
            "Florida man tries to pay bail with stack of expired Taco Bell coupons",
        ][:count]

        # Save to database
        formatted = [
            {"text": headline, "is_real": False, "source_url": None}
            for headline in fake_headlines
        ]

        result = save_headlines_to_db(formatted)
        return f"Generated {len(fake_headlines)} fake headlines\n\n{result}"

    agent = AssistantAgent(
        name="generator_agent",
        model_client=model_client,
        system_message="""You are a creative writer specializing in generating fake but believable Florida Man headlines.

Your job:
1. Study real Florida Man headlines to understand the style
2. Generate absurd but plausible fake headlines
3. Make them indistinguishable from real ones
4. Save them to the database

Keep headlines under 100 characters and maintain the chaotic Florida Man energy.""",
        description="Generates fake Florida Man headlines",
        tools=[generate_fake_headlines, get_db_stats],
    )

    return agent
