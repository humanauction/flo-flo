from pydantic_settings import BaseSettings


class AgentConfig(BaseSettings):
    """AutoGen agent configuration"""

    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"
    max_headlines_per_scrape: int = 10
    target_url: str = "https://floridaman.com/"

    class Config:
        env_file = "../backend/.env"
        env_file_encoding = "utf-8"
        case_sensitive = False


config = AgentConfig()
