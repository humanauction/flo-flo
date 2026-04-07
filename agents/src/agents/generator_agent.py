
import asyncio
import logging
import re
import threading
from collections.abc import Callable
from typing import Any, Protocol

from autogen_agentchat.agents import AssistantAgent
from autogen_core.models import SystemMessage, UserMessage
from autogen_ext.models.openai import OpenAIChatCompletionClient

from agents.tools.generator_quality import (
    GeneratorQualityStats,
    apply_quality_filters,
)

logger = logging.getLogger(__name__)

TEMPLATE_HEADLINES: list[str] = [
    "Florida man attempts to ride shopping cart down I-95 during rush hour",
    "Florida man arrested for teaching pet iguana to shoplift at 7-Eleven",
    "Florida man builds treehouse in Walmart parking lot, "
    "claims squatter's rights",
    "Florida man caught using fishing rod to steal donuts from bakery window",
    "Florida man tries to pay bail with stack of expired Taco Bell coupons",
    "Florida man starts fire trying to cook eggs with a clothes iron",
    "Florida man arrested for breaking into jail to visit friends",
    "Florida man uses alligator to shotgun a beer at party",
    "Florida man calls 911 to report his stolen drugs",
    "Florida man caught driving stolen golf cart to liquor store",
]

MAX_OPENAI_GENERATION_COUNT = 50  # for future OpenAI-primary mode
_OPENAI_PROVIDER = "openai_primary"
_TEMPLATE_PROVIDER = "template_fallback"
_LINE_PREFIX_RE = re.compile(r"^\s*(?:[-*•]+|\d+[.)])\s*")


def _template_provider(count: int) -> list[str]:
    return TEMPLATE_HEADLINES[:count]


def _validate_count(count: object, max_count: int) -> str | None:
    if isinstance(count, bool):
        return "Invalid count: bool is not allowed; provide an integer"
    if not isinstance(count, int):
        return "Invalid count: must be an integer"
    if count < 1 or count > max_count:
        return f"Invalid count: must be between 1 and {max_count}"
    return None


def _default_save_headlines_to_db(payload: list[dict[str, Any]]) -> str:
    from agents.tools.database import save_headlines_to_db
    return save_headlines_to_db(payload)


def _get_db_stats_tool() -> Callable[[], str]:
    from agents.tools.database import get_db_stats
    return get_db_stats


def _build_model_client() -> OpenAIChatCompletionClient:
    from agents.config import config

    if not config.openai_api_key or config.openai_api_key == "your_key_here":
        raise ValueError(
            "OPENAI_API_KEY is required to create generator agent for OpenAI mode"
        )

    return OpenAIChatCompletionClient(
        model=config.openai_model,
        api_key=config.openai_api_key,
    )


def _extract_headlines_from_model_text(text: str, limit: int) -> list[str]:
    lines: list[str] = []
    for raw in text.splitlines():
        clean = _LINE_PREFIX_RE.sub("", raw).strip().strip('"').strip("'")
        if clean:
            lines.append(clean)

    if not lines and text.strip():
        lines = [text.strip().strip('"').strip("'")]

    deduped: list[str] = []
    seen: set[str] = set()
    for item in lines:
        key = item.lower()
        if key not in seen:
            seen.add(key)
            deduped.append(item)

    return deduped[:limit]


class _ModelClientLike(Protocol):
    async def create(
            self,
            messages: list[SystemMessage | UserMessage],
    ) -> Any: ...


async def _openai_provider(
    model_client: _ModelClientLike,
    count: int,
) -> list[str]:
    messages = [
        SystemMessage(
            content=(
                "You generate fictional but plausible Florida Man headlines. "
                "Each headline must include the phrase 'Florida man'. "
                "Return only headlines, one per line, no extra commentary."
            )
        ),
        UserMessage(
            source="generator_agent",
            content=f"Generate {count} unique fake headlines.",
        ),
    ]
    result = await model_client.create(messages=messages)
    content = getattr(result, "content", None)
    if not isinstance(content, str):
        return []
    return _extract_headlines_from_model_text(content, limit=count)


def _run_coro_blocking(coro):
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(coro)

    box: dict[str, Any] = {}
    err: dict[str, BaseException] = {}

    def runner() -> None:
        try:
            box["value"] = asyncio.run(coro)
        except BaseException as exc:
            err["error"] = exc

    thread = threading.Thread(target=runner, daemon=True)
    thread.start()
    thread.join()

    if "error" in err:
        raise err["error"]
    return box.get("value")


def generate_fake_headlines_sync(
    count: int = 5,
    *,
    headline_provider: Callable[[int], list[str]] = _template_provider,
    max_count: int | None = None,
    quality_fn: Callable[[list[str]], tuple[list[str], GeneratorQualityStats]] = apply_quality_filters,
    save_fn: Callable[[list[dict[str, Any]]], str] = _default_save_headlines_to_db,
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
    model_client = _build_model_client()
    db_stats_tool = _get_db_stats_tool()

    def generate_fake_headlines(count: int = 5) -> str:
        try:
            validation_error = _validate_count(count, MAX_OPENAI_GENERATION_COUNT)
            if validation_error:
                return validation_error

            provider = _OPENAI_PROVIDER
            raw_headlines: list[str] = []

            try:
                raw_headlines = _run_coro_blocking(
                    _openai_provider(model_client=model_client, count=count)
                ) or []
            except Exception as exc:
                logger.warning("OpenAI generation failed, falling back to templates: %s", exc)
                provider = _TEMPLATE_PROVIDER

            if not raw_headlines:
                raw_headlines = _template_provider(count)
                provider = _TEMPLATE_PROVIDER

            summary = generate_fake_headlines_sync(
                count=count,
                headline_provider=lambda _requested: raw_headlines,
                max_count=MAX_OPENAI_GENERATION_COUNT,
            )
            return f"{summary}\nProvider: {provider}"

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
        tools=[generate_fake_headlines, db_stats_tool],
    )
