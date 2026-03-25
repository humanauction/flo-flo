import os
import pytest

pytestmark = [pytest.mark.external, pytest.mark.openai]


@pytest.mark.skipif(
    not os.getenv("OPENAI_API_KEY"),
    reason="OPENAI_API_KEY not set",
)
def test_generator_with_real_openai():
    ...


def smoketest_generator_agent():
    assert True
