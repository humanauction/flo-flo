from pathlib import Path

from pydantic_settings import BaseSettings


class AgentConfig(BaseSettings):
    """AutoGen agent configuration."""

    openai_api_key: str
    openai_model: str = "gpt-4o-mini"
    max_headlines_per_scrape: int = 10
    target_url: str = "https://floridaman.com/"
    track_tokens: bool = True

    class Config:
        # agents/src/agents/config.py -> repo root is parents[3]
        env_file = str(
            Path(__file__).resolve().parents[3] / "backend" / ".env"
        )
        env_file_encoding = "utf-8"
        case_sensitive = False
        extra = "ignore"


config = AgentConfig()  # type: ignore
