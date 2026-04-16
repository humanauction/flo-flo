import asyncio
import json
import logging
import re
import threading
from collections.abc import Callable
from typing import Annotated, Any, Protocol

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
OPENAI_PROVIDER_TIMEOUT_SECONDS = 12.0
DEFAULT_CONTEXT_ROWS = 3
PROVENANCE_SCHEMA_VERSION = 1
MAX_CONTEXT_CANDIDATES = 12


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
    try:
        from agents.config import config
    except Exception as exc:
        logger.error("Failed to import config", exc_info=True)
        raise RuntimeError(
            "Generator configuration error: could not load agent config."
        ) from exc

    api_key = getattr(config, "openai_api_key", None)
    model = getattr(config, "openai_model", None)

    if (
        not isinstance(api_key, str)
        or not api_key.strip()
        or api_key == "your_key_here"
    ):
        raise RuntimeError(
            "Generator configuration error: "
            "OPENAI_API_KEY missing or placeholder."
        )
    if not isinstance(model, str) or not model.strip():
        raise RuntimeError(
            "Generator configuration error: OPENAI_MODEL missing."
        )

    try:
        return OpenAIChatCompletionClient(model=model, api_key=api_key)
    except Exception as exc:
        logger.error("Failed to initialize OpenAI client", exc_info=True)
        raise RuntimeError(
            "Generator configuration error: "
            "failed to initialize OpenAI client."
        ) from exc


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
    recent_real_context: list[dict[str, Any]] | None = None,
) -> list[str]:
    context_json = _context_rows_to_prompt_json(
        recent_real_context or []
    )

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
            content=(
                f"Generate {count} unique fake headlines.\n"
                "Use recent real context for topical grounding only.\n"
                "Do not copy or closely paraphrase context headlines.\n"
                f"Recent real context JSON: {context_json}"
            ),
        ),
    ]
    result = await model_client.create(messages=messages)
    content = getattr(result, "content", None)
    if not isinstance(content, str):
        return []
    return _extract_headlines_from_model_text(content, limit=count)


def _run_coro_blocking(
    coro,
    *,
    timeout_seconds: float = OPENAI_PROVIDER_TIMEOUT_SECONDS,
):
    if timeout_seconds <= 0:
        raise ValueError("Timeout must be greater than 0")

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
    thread.join(timeout=timeout_seconds)

    if thread.is_alive():
        raise TimeoutError(
            f"Operation timed out after {timeout_seconds:.1f}s"
        )

    if "error" in err:
        raise err["error"]
    return box.get("value")


def generate_fake_headlines_sync(
    count: int = 5,
    *,
    headline_provider: Callable[[int], list[str]] = _template_provider,
    max_count: int | None = None,
    quality_fn:
    Callable[
        [list[str]], tuple[list[str], GeneratorQualityStats]
    ] = apply_quality_filters,
    save_fn:
    Callable[
        [list[dict[str, Any]]], str
    ] = _default_save_headlines_to_db,
) -> str:
    effective_max = (
        max_count if max_count is not None else len(TEMPLATE_HEADLINES)
    )

    validation_error = _validate_count(count, effective_max)
    if validation_error:
        return validation_error

    requested = count
    raw_headlines = headline_provider(requested)[:requested]
    provider_input_count = len(raw_headlines)
    filtered_headlines, quality = quality_fn(raw_headlines)

    provider_shortfall = max(0, requested - provider_input_count)
    quality_dropped = max(
        0, provider_input_count - len(filtered_headlines)
    )

    notices: list[str] = []
    if provider_shortfall > 0:
        notices.append(
            "Notice: provider shortfall "
            f"{provider_shortfall} "
            f"(requested={requested}, provider_input={provider_input_count})"
        )
    if quality_dropped > 0:
        notices.append(
            f"Notice: requested={requested}, "
            f"generated={len(filtered_headlines)} "
            f"(quality dropped {quality_dropped})"
        )

    if not filtered_headlines:
        msg = (
            "Generation produced no valid headlines after quality checks "
            f"(requested={requested}, input={quality['input_count']}, kept=0)"
        )
        if notices:
            msg += "\n" + "\n".join(notices)
        return msg

    payload = [
        {"text": headline, "is_real": False, "source_url": None}
        for headline in filtered_headlines
    ]
    save_result = save_fn(payload)

    summary = (
        f"Generated {len(filtered_headlines)} fake headlines "
        f"(requested {requested})\n\n"
        f"{save_result}\n"
        f"Quality: input={quality['input_count']}, "
        f"kept={quality['kept_count']}, "
        f"invalid={quality['invalid_dropped']}, "
        f"duplicates={quality['duplicates_dropped']}"
    )

    if notices:
        summary += "\n" + "\n".join(notices)

    return summary


def _get_recent_real_context(
    limit: int = DEFAULT_CONTEXT_ROWS,
) -> list[dict[str, Any]]:
    from agents.tools.database import get_recent_real_headline_context

    try:
        rows = get_recent_real_headline_context(limit=limit)
    except Exception as exc:
        logger.warning("Recent real context fetch failed: %s", exc)
        return []

    if not isinstance(rows, list):
        return []

    return [row for row in rows if isinstance(row, dict)]


def _normalize_context_text(value: str) -> str:
    return " ".join(value.lower().split())


def _source_bucket(source_url: Any) -> str:
    if not isinstance(source_url, str) or not source_url.strip():
        return "unknown"
    from urllib.parse import urlparse
    host = urlparse(source_url).netloc.lower().strip()
    return host or "unknown"


def _context_sort_key(row: dict[str, Any]) -> tuple[str, int, str]:
    created_at = row.get("created_at")
    created = created_at if isinstance(created_at, str) else ""
    headline_id = row.get("headline_id")
    hid = headline_id if isinstance(headline_id, int) else -1
    text = row.get("text")
    txt = text.lower() if isinstance(text, str) else ""
    return (created, hid, txt)


def _select_deterministic_context(
    candidates: list[dict[str, Any]],
    *,
    cap: int = DEFAULT_CONTEXT_ROWS,
) -> list[dict[str, Any]]:
    if cap < 1:
        return []

    valid: list[dict[str, Any]] = []
    seen_norm: set[str] = set()

    for row in candidates:
        if not isinstance(row, dict):
            continue
        text = row.get("text")
        if not isinstance(text, str):
            continue
        cleaned = " ".join(text.split()).strip()
        if len(cleaned) < 12:
            continue

        norm = _normalize_context_text(cleaned)
        if norm in seen_norm:
            continue
        seen_norm.add(norm)

        valid.append(
            {
                "headline_id": row.get("headline_id"),
                "text": cleaned,
                "source_url": row.get("source_url"),
                "created_at": row.get("created_at"),
            }
        )

    valid.sort(key=_context_sort_key, reverse=True)

    selected: list[dict[str, Any]] = []
    selected_norms: set[str] = set()
    used_sources: set[str] = set()

    for row in valid:
        source = _source_bucket(row.get("source_url"))
        norm = _normalize_context_text(row["text"])
        if source in used_sources or norm in selected_norms:
            continue
        selected.append(row)
        used_sources.add(source)
        selected_norms.add(norm)
        if len(selected) >= cap:
            return selected

    for row in valid:
        norm = _normalize_context_text(row["text"])
        if norm in selected_norms:
            continue
        selected.append(row)
        selected_norms.add(norm)
        if len(selected) >= cap:
            break

    return selected


def _compact_context_rows(
    rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    compact: list[dict[str, Any]] = []

    for row in rows:
        text = row.get("text")
        if not isinstance(text, str) or not text.strip():
            continue

        compact.append(
            {
                "headline_id": row.get("headline_id"),
                "text": text.strip(),
                "source_url": row.get("source_url"),
                "created_at": row.get("created_at"),
            }
        )

    return compact


def _context_rows_to_prompt_json(rows: list[dict[str, Any]]) -> str:
    return json.dumps(_compact_context_rows(rows), ensure_ascii=True)


def _build_provenance_payload(
    *,
    provider: str,
    requested_count: int,
    recent_real_context: list[dict[str, Any]],
) -> dict[str, Any]:
    compact_rows = _compact_context_rows(recent_real_context)
    return {
        "schema_version": PROVENANCE_SCHEMA_VERSION,
        "provider": provider,
        "requested_count": requested_count,
        "recent_real_context_count": len(compact_rows),
        "recent_real_context": compact_rows,
    }


def _append_provenance_to_summary(
    summary: str,
    *,
    provider: str,
    requested_count: int,
    recent_real_context: list[dict[str, Any]],
) -> str:
    payload = _build_provenance_payload(
        provider=provider,
        requested_count=requested_count,
        recent_real_context=recent_real_context,
    )
    payload_json = json.dumps(payload, ensure_ascii=True, sort_keys=True)
    return f"{summary}\nProvider: {provider}\nProvenance: {payload_json}"


def create_generator_agent() -> AssistantAgent:
    model_client = _build_model_client()
    db_stats_tool = _get_db_stats_tool()

    def generate_fake_headlines(
        count: Annotated[
            int,
            "Number of fake headlines to generate. "
            "Must be an integer "
            f"between 1 and {MAX_OPENAI_GENERATION_COUNT}.",
        ] = 5,
    ) -> str:
        try:
            validation_error = _validate_count(
                count,
                MAX_OPENAI_GENERATION_COUNT
            )
            if validation_error:
                return validation_error

            provider = _OPENAI_PROVIDER
            raw_headlines: list[str] = []
            recent_real_candidates = _get_recent_real_context(
                limit=MAX_CONTEXT_CANDIDATES
            )
            recent_real_context = _select_deterministic_context(
                recent_real_candidates,
                cap=DEFAULT_CONTEXT_ROWS,
            )

            try:
                raw_headlines = _run_coro_blocking(
                    _openai_provider(
                        model_client=model_client,
                        count=count,
                        recent_real_context=recent_real_context,
                    )
                ) or []
            except TimeoutError as exc:
                logger.warning("%s. Falling back to templates.", exc)
                provider = _TEMPLATE_PROVIDER
            except Exception as exc:
                logger.warning(
                    "OpenAI generation failed, falling back to templates: %s",
                    exc,
                )
                provider = _TEMPLATE_PROVIDER

            if not raw_headlines:
                raw_headlines = _template_provider(count)
                provider = _TEMPLATE_PROVIDER

            summary = generate_fake_headlines_sync(
                count=count,
                headline_provider=lambda _requested: raw_headlines,
                max_count=MAX_OPENAI_GENERATION_COUNT,
            )
            return _append_provenance_to_summary(
                summary,
                provider=provider,
                requested_count=count,
                recent_real_context=recent_real_context,
            )

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
