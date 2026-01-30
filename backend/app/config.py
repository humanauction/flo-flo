from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator
from typing import List, Union


class Settings(BaseSettings):
    """Application settings loaded from .env file"""

    database_url: str = "sqlite:///./floridaman.db"
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_reload: bool = True
    allowed_origins: Union[List[str], str] = ["http://localhost:3000"]
    openai_api_key: str = ""

    @field_validator("allowed_origins", mode="before")
    @classmethod
    def parse_origins(cls, v):
        """Parse ALLOWED_ORIGINS from various formats"""
        if isinstance(v, str):
            # Handle comma-separated string
            return [origin.strip() for origin in v.split(",")]
        return v

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False
    )


settings = Settings()
