import json
import os
import re
import pytest
from types import SimpleNamespace


def _has_real_openai_key() -> bool:
    key = os.getenv("OPENAI_API_KEY", "").strip()
    if not key:
        try:
            from agents.config import config
            key = str(getattr(config, "openai_api_key", "")).strip()
        except Exception:
            key = ""

    return bool(
        key
        and key != "your_key_here"
        and key.startswith("sk-")
    )


def _collect_text_chunks(event) -> list[str]:
    chunks: list[str] = []

    for attr in ("content", "text"):
        value = getattr(event, attr, None)
        if isinstance(value, str) and value.strip():
            chunks.append(value.strip())

    msg = getattr(event, "message", None)
    if msg is not None:
        for attr in ("content", "text"):
            value = getattr(msg, attr, None)
            if isinstance(value, str) and value.strip():
                chunks.append(value.strip())

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


def test_extract_headlines_from_model_text_parses_numbered_lines():
    from agents.generator_agent import _extract_headlines_from_model_text

    text = """
    1. Florida man builds raft from pizza boxes
    2) Florida man wrestles mailbox over parking spot
    - Florida man starts kayak traffic school
    """
    headlines = _extract_headlines_from_model_text(text, limit=3)
    assert headlines == [
        "Florida man builds raft from pizza boxes",
        "Florida man wrestles mailbox over parking spot",
        "Florida man starts kayak traffic school",
    ]


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
    assert (
        "saved" in normalized
        or "skipped" in normalized
        or "invalid" in normalized
    )
    assert normalized not in {"done", "complete", "completed", "ok", "success"}
    assert len(normalized) > 20
    assert "provider: openai_primary" in normalized
    assert "provider: template_fallback" not in normalized
    assert "generation failed:" not in normalized
    assert "generated 1 fake headlines (requested 1)" in normalized
    assert re.search(r"saved \d+ new headlines", normalized)
    assert re.search(
        r"quality:\sinput=1,\skept=1,\sinvalid=0,\sduplicates=0",
        normalized,
    )

    provenance_lines = [
        line for line in full_text.splitlines()
        if line.startswith("Provenance: ")
    ]
    assert len(provenance_lines) == 1

    provenance = json.loads(
        provenance_lines[0][len("Provenance: "):]
    )
    assert provenance["schema_version"] == 1
    assert provenance["provider"] == "openai_primary"
    assert provenance["requested_count"] == 1
    assert isinstance(provenance["recent_real_context"], list)
    assert provenance["recent_real_context_count"] == len(
        provenance["recent_real_context"]
    )
    if provenance["recent_real_context"]:
        assert "is_real" not in provenance["recent_real_context"][0]


def test_generate_fake_headlines_rejects_bool_count():
    from agents.generator_agent import generate_fake_headlines_sync

    output = generate_fake_headlines_sync(True)
    assert output == "Invalid count: bool is not allowed; provide an integer"


def test_generate_fake_headlines_rejects_count_above_template_capacity():
    from agents.generator_agent import (
        TEMPLATE_HEADLINES,
        generate_fake_headlines_sync,
    )

    output = generate_fake_headlines_sync(len(TEMPLATE_HEADLINES) + 1)
    assert output == (
        f"Invalid count: must be between 1 and {len(TEMPLATE_HEADLINES)}"
    )


def test_generate_fake_headlines_quality_summary_format_contract():
    from agents.generator_agent import generate_fake_headlines_sync

    duplicate_templates = [
        "Florida man does one believable and weird thing for local TV cameras",
        "  florida man does one believable and weird thing "
        "for local TV cameras  ",
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


def test_sync_generation_path_does_not_require_openai_key(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    from agents.generator_agent import generate_fake_headlines_sync

    output = generate_fake_headlines_sync(
        count=1,
        save_fn=lambda payload: f"Saved {len(payload)} new headlines",
    )
    assert "Generated 1 fake headlines" in output


@pytest.mark.asyncio
async def test_openai_provider_parses_string_content():
    from agents.generator_agent import _openai_provider

    class FakeClient:
        async def create(self, messages: object):
            return SimpleNamespace(
                content="1. Florida man invents swamp-powered treadmill\n "
                "2. Florida man opens alligator yoga studio",
            )

    headlines = await _openai_provider(FakeClient(), count=2)
    assert headlines == [
        "Florida man invents swamp-powered treadmill",
        "Florida man opens alligator yoga studio",
    ]


@pytest.mark.asyncio
async def test_openai_provider_returns_empty_when_content_not_string():
    from agents.generator_agent import _openai_provider

    class FakeClient:
        async def create(self, messages: object):
            return SimpleNamespace(content=[])

    headlines = await _openai_provider(FakeClient(), count=2)
    assert headlines == []


def test_generate_fake_headlines_reports_provider_shortfall():
    from agents.generator_agent import (
        MAX_OPENAI_GENERATION_COUNT,
        generate_fake_headlines_sync,
    )

    supplied = [
        (
            "Florida man causes unusual incident number "
            f"{i} at county fair parking lot"
        )
        for i in range(10)
    ]

    output = generate_fake_headlines_sync(
        count=12,
        max_count=MAX_OPENAI_GENERATION_COUNT,
        headline_provider=lambda _count: supplied,
        save_fn=lambda payload: f"Saved {len(payload)} new headlines",
    )

    assert "Generated 10 fake headlines (requested 12)" in output
    assert (
        "Notice: provider shortfall 2 (requested=12, provider_input=10)"
        in output
    )


def test_append_provenance_to_summary_includes_single_json_object():
    from agents.generator_agent import _append_provenance_to_summary

    base_summary = (
        "Generated 1 fake headlines (requested 1)\n"
        "Saved 1 new headlines"
    )
    context_rows = [
        {
            "headline_id": 101,
            "text": "Florida man real context one",
            "source_url": "https://example.com/one",
            "created_at": "2026-04-14T12:00:00+00:00",
            "is_real": True,
        }
    ]

    output = _append_provenance_to_summary(
        base_summary,
        provider="openai_primary",
        requested_count=1,
        recent_real_context=context_rows,
    )

    assert "Provider: openai_primary" in output

    provenance_lines = [
        line for line in output.splitlines()
        if line.startswith("Provenance: ")
    ]
    assert len(provenance_lines) == 1

    payload = json.loads(provenance_lines[0][len("Provenance: "):])
    assert payload["schema_version"] == 1
    assert payload["provider"] == "openai_primary"
    assert payload["requested_count"] == 1
    assert payload["recent_real_context_count"] == 1
    assert payload["recent_real_context"][0]["headline_id"] == 101
    assert "is_real" not in payload["recent_real_context"][0]


def test_select_deterministic_context_filters_dedupes_diversity_and_order():
    from agents.generator_agent import _select_deterministic_context

    candidates = [
        {
            "headline_id": 900,
            "text": "too short",
            "source_url": "https://junk.example/ignored",
            "created_at": "2026-04-16T10:06:00+00:00",
        },
        {
            "headline_id": 610,
            "text": "Florida man opens emergency kayak lane on freeway",
            "source_url": "https://a.example/one",
            "created_at": "2026-04-16T10:05:00+00:00",
        },
        {
            "headline_id": 609,
            "text": "  florida   MAN opens emergency kayak lane on freeway  ",
            "source_url": "https://z.example/dup",
            "created_at": "2026-04-16T10:04:59+00:00",
        },
        {
            "headline_id": 608,
            "text": "Florida man installs snack alarm at city pier",
            "source_url": "https://a.example/two",
            "created_at": "2026-04-16T10:04:00+00:00",
        },
        {
            "headline_id": 607,
            "text": "Florida man launches bait drone over marsh",
            "source_url": "https://b.example/one",
            "created_at": "2026-04-16T10:03:00+00:00",
        },
        {
            "headline_id": 606,
            "text": "Florida man starts alligator choir downtown",
            "source_url": "https://c.example/one",
            "created_at": "2026-04-16T10:02:00+00:00",
        },
    ]

    first = _select_deterministic_context(candidates, cap=3)
    second = _select_deterministic_context(candidates, cap=3)

    # Deterministic and stable ordering.
    assert first == second
    assert [row["headline_id"] for row in first] == [610, 607, 606]

    # Invalid short row dropped.
    assert all(row["headline_id"] != 900 for row in first)

    # Normalized duplicate dropped.
    assert all(row["headline_id"] != 609 for row in first)

    # Source diversity preferred before same-source fill.
    hosts = [row["source_url"].split("/")[2] for row in first]
    assert len(set(hosts)) == 3
