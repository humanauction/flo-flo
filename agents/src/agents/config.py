from pathlib import Path

from pydantic_settings import BaseSettings


class AgentConfig(BaseSettings):
    """AutoGen agent configuration."""

    openai_api_key: str
    openai_model: str = "gpt-4o-mini"
    max_headlines_per_scrape: int = 10
    target_url: str = "https://floridaman.com/"
    track_tokens: bool = True
    scrape_enabled_sources: str = "floridaman_primary,fallback_static"
    scrape_source_max_items: int = 10
    scrape_min_headline_chars: int = 12
    scrape_require_florida_keyword: bool = True

    class Config:
        # agents/src/agents/config.py -> repo root is parents[3]
        env_file = str(
            Path(__file__).resolve().parents[3] / "backend" / ".env"
        )
        env_file_encoding = "utf-8"
        case_sensitive = False
        extra = "ignore"


config = AgentConfig()  # type: ignore
