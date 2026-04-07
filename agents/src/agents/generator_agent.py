import logging
from collections.abc import Callable
from typing import Any

from autogen_agentchat.agents import AssistantAgent
from autogen_ext.models.openai import OpenAIChatCompletionClient

from agents.config import config
from agents.tools.database import get_db_stats, save_headlines_to_db
from agents.tools.generator_quality import GeneratorQualityStats, apply_quality_filters

logger = logging.getLogger(__name__)

TEMPLATE_HEADLINES: list[str] = [
    "Florida man attempts to ride shopping cart down I-95 during rush hour",
    "Florida man arrested for teaching pet iguana to shoplift at 7-Eleven",
    "Florida man builds treehouse in Walmart parking lot, claims squatter's rights",
    "Florida man caught using fishing rod to steal donuts from bakery window",
    "Florida man tries to pay bail with stack of expired Taco Bell coupons",
    "Florida man starts fire trying to cook eggs with a clothes iron",
    "Florida man arrested for breaking into jail to visit friends",
    "Florida man uses alligator to shotgun a beer at party",
    "Florida man calls 911 to report his stolen drugs",
    "Florida man caught driving stolen golf cart to liquor store",
]

MAX_OPENAI_GENERATION_COUNT = 50  # for TODO future OpenAI-primary mode


def _template_provider(count: int) -> list[str]:
    """Provide fake headlines from hardcoded templates."""
    return TEMPLATE_HEADLINES[:count]


def _validate_count(count: object, max_count: int) -> str | None:
    if isinstance(count, bool):
        return "Invalid count: bool is not allowed; provide an integer"
    if not isinstance(count, int):
        return "Invalid count: must be an integer"
    if count < 1 or count > max_count:
        return f"Invalid count: must be between 1 and {max_count}"
    return None


def generate_fake_headlines_sync(
    count: int = 5,
    *,
    headline_provider: Callable[[int], list[str]] = _template_provider,
    max_count: int | None = None,
    quality_fn: Callable[
        [list[str]], tuple[list[str], GeneratorQualityStats]
    ] = apply_quality_filters,
    save_fn: Callable[[list[dict[str, Any]]], str] = save_headlines_to_db,
) -> str:
    effective_max = max_count if max_count is not None else len(TEMPLATE_HEADLINES)

    validation_error = _validate_count(count, effective_max)
    if validation_error:
        return validation_error

    requested = count
    raw_headlines = headline_provider(requested)[:requested]
    filtered_headlines, quality = quality_fn(raw_headlines)

    if not filtered_headlines:
        return (
            "Generation produced no valid headlines after quality checks "
            f"(requested={requested}, input={quality['input_count']}, kept=0)"
        )

    payload = [
        {"text": headline, "is_real": False, "source_url": None}
        for headline in filtered_headlines
    ]
    save_result = save_fn(payload)

    summary = (
        f"Generated {len(filtered_headlines)} fake headlines (requested {requested})\n\n"
        f"{save_result}\n"
        f"Quality: input={quality['input_count']}, "
        f"kept={quality['kept_count']}, "
        f"invalid={quality['invalid_dropped']}, "
        f"duplicates={quality['duplicates_dropped']}"
    )

    if len(filtered_headlines) != requested:
        summary += (
            f"\nNotice: requested={requested}, generated={len(filtered_headlines)} "
            f"(quality dropped {requested - len(filtered_headlines)})"
        )

    return summary


def create_generator_agent() -> AssistantAgent:
    """Create the fake headline generator agent."""

    model_client = OpenAIChatCompletionClient(
        model=config.openai_model,
        api_key=config.openai_api_key,
    )

    def generate_fake_headlines(count: int = 5) -> str:
        """Generate fake Florida Man headlines - SYNC function."""
        try:
            logger.info("Generating %s fake headlines...", count)
            # Template mode (truthful max = len(TEMPLATE_HEADLINES))
            return generate_fake_headlines_sync(count=count)

            # Future OpenAI-primary mode:
            # return generate_fake_headlines_sync(
            #     count=count,
            #     headline_provider=openai_provider,
            #     max_count=MAX_OPENAI_GENERATION_COUNT,
            # )
        except Exception as e:
            logger.error("Generator tool failed: %s", e, exc_info=True)
            return f"Generation failed: {str(e)}"

    return AssistantAgent(
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
