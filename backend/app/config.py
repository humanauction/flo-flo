from pathlib import Path
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
    openai_api_key: str = ""  # Default empty to avoid Pylance error

    @field_validator("allowed_origins", mode="before")
    @classmethod
    def parse_origins(cls, v):
        """Parse ALLOWED_ORIGINS from various formats"""
        if isinstance(v, str):
            # Handle comma-separated string
            return [origin.strip() for origin in v.split(",")]
        return v

    @field_validator("database_url", mode="before")
    @classmethod
    def normalize_database_url(cls, v):
        if not isinstance(v, str):
            return v

        prefix = "sqlite:///"
        if not v.startswith(prefix):
            return v

        db_part = v[len(prefix):]
        if db_part in ("", ":memory:"):
            return v

        db_path = Path(db_part)
        if db_path.is_absolute():
            return v

        backend_dir = Path(__file__).resolve().parents[1]
        abs_db = (backend_dir / db_path).resolve()
        return f"sqlite:///{abs_db.as_posix()}"

    model_config = SettingsConfigDict(
        env_file=str(Path(__file__).parent.parent / ".env"),
        env_file_encoding="utf-8",
        case_sensitive=False
    )


settings = Settings()

