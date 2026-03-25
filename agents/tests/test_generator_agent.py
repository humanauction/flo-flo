import os
import pytest

pytestmark = [pytest.mark.external, pytest.mark.openai]


def _has_real_openai_key() -> bool:
    key = os.getenv("OPENAI_API_KEY", "").strip()
    return bool(
        key
        and key != "your_key_here"
        and key.startswith("sk-")
    )


@pytest.mark.skipif(
    not _has_real_openai_key(),
    reason="OPENAI_API_KEY missing; skipping OpenAI integration test",
)
@pytest.mark.asyncio
async def test_generator_agent_with_real_openai_runs_stream():
    # Import inside test so missing key/config doesn't break collection.
    from agents.generator_agent import create_generator_agent

    agent = create_generator_agent()

    saw_output = False
    task = (
        "You must call your generate_fake_headlines tool with count=1, "
        "then report completion in one short sentence."
    )

    async for _event in agent.run_stream(task=task):
        saw_output = True

    assert saw_output is True
