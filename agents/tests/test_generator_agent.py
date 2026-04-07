import os
import re
import pytest

pytestmark = [pytest.mark.external, pytest.mark.openai]


def _has_real_openai_key() -> bool:
    key = os.getenv("OPENAI_API_KEY", "").strip()
    return bool(
        key
        and key != "your_key_here"
        and key.startswith("sk-")
    )


def _collect_text_chunks(event) -> list[str]:
    chunks: list[str] = []

    # Common direct fields on events/messages
    for attr in ("content", "text"):
        value = getattr(event, attr, None)
        if isinstance(value, str) and value.strip():
            chunks.append(value.strip())

    # Some events carry a nested message object
    msg = getattr(event, "message", None)
    if msg is not None:
        for attr in ("content", "text"):
            value = getattr(msg, attr, None)
            if isinstance(value, str) and value.strip():
                chunks.append(value.strip())

    # Some events carry a list of messages
    messages = getattr(event, "messages", None)
    if isinstance(messages, list):
        for item in messages:
            if isinstance(item, str) and item.strip():
                chunks.append(item.strip())
                continue
            for attr in ("content", "text"):
                value = getattr(item, attr, None)
                if isinstance(value, str) and value.strip():
                    chunks.append(value.strip())

    return chunks


@pytest.mark.skipif(
    not _has_real_openai_key(),
    reason="OPENAI_API_KEY missing; skipping OpenAI integration test",
)
@pytest.mark.asyncio
async def test_generator_agent_with_real_openai_output_quality_shape():
    # Import inside test so missing key/config doesn't break collection.
    from agents.generator_agent import create_generator_agent

    agent = create_generator_agent()

    chunks: list[str] = []
    task = (
        "You must call your generate_fake_headlines tool with count=1. "
        "Return only the tool result summary."
    )

    async for event in agent.run_stream(task=task):
        chunks.extend(_collect_text_chunks(event))

    full_text = "\n".join(chunks).strip()
    assert full_text, "Expected non-empty streamed output"

    normalized = " ".join(full_text.lower().split())

    # Current contract checks (until headline-text contract enhancement lands)
    # TODO(phase-3.4): Reintroduce a headline-like assertion (e.g. contains
    # 'Florida man') once the generator tool returns explicit headline lines.
    assert "generated" in normalized, (
        "Expected generated-count signal in output"
    )
    assert (
        "saved" in normalized or
        "skipped" in normalized or
        "invalid" in normalized
    ), "Expected persistence/result signal in output"

    trivial_only = {"done", "complete", "completed", "ok", "success"}
    assert normalized not in trivial_only, (
        "Output was only a trivial confirmation"
    )
    assert len(normalized) > 20, (
        "Output too short to represent a meaningful result"
    )

@pytest.mark.external
@pytest.mark.openai
@pytest.mark.skipif(
    not _has_real_openai_key(),
    reason="OPENAI_API_KEY missing; skipping OpenAI integration test",
)
@pytest.mark.asyncio
async def test_generator_agent_with_real_openai_output_quality_shape():
    from agents.generator_agent import create_generator_agent

    agent = create_generator_agent()

    chunks: list[str] = []
    task = (
        "You must call your generate_fake_headlines tool with count=1. "
        "Return only the tool result summary."
    )

    async for event in agent.run_stream(task=task):
        chunks.extend(_collect_text_chunks(event))

    full_text = "\n".join(chunks).strip()
    assert full_text, "Expected non-empty streamed output"

    normalized = " ".join(full_text.lower().split())

    assert "generated" in normalized
    assert ("saved" in normalized or "skipped" in normalized or "invalid" in normalized)
    assert normalized not in {"done", "complete", "completed", "ok", "success"}
    assert len(normalized) > 20


def test_generate_fake_headlines_rejects_bool_count():
    from agents.generator_agent import generate_fake_headlines_sync

    output = generate_fake_headlines_sync(True)
    assert output == "Invalid count: bool is not allowed; provide an integer"


def test_generate_fake_headlines_rejects_count_above_template_capacity():
    from agents.generator_agent import TEMPLATE_HEADLINES, generate_fake_headlines_sync

    output = generate_fake_headlines_sync(len(TEMPLATE_HEADLINES) + 1)
    assert output == (
        f"Invalid count: must be between 1 and {len(TEMPLATE_HEADLINES)}"
    )


def test_generate_fake_headlines_quality_summary_format_contract():
    from agents.generator_agent import generate_fake_headlines_sync

    duplicate_templates = [
        "Florida man does one believable and weird thing for local TV cameras",
        "  florida man does one believable and weird thing for local TV cameras  ",
    ]

    output = generate_fake_headlines_sync(
        count=2,
        headline_provider=lambda _count: duplicate_templates,
        save_fn=lambda payload: f"Saved {len(payload)} new headlines",
    )

    assert "Generated 1 fake headlines (requested 2)" in output
    assert "Notice: requested=2, generated=1 (quality dropped 1)" in output
    assert re.search(
        r"Quality:\s*input=\d+,\s*kept=\d+,\s*invalid=\d+,\s*duplicates=\d+",
        output,
    )