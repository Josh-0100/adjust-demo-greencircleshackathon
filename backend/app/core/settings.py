from pathlib import Path
from typing import Literal

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = Path(__file__).resolve().parents[3]
BOROUGHS = ["Bolton", "Bury", "Manchester", "Oldham", "Rochdale", "Salford", "Stockport", "Tameside", "Trafford", "Wigan"]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=str(PROJECT_ROOT / ".env"), extra="ignore", case_sensitive=False)
    demo_mode: bool = True
    database_url: str = f"sqlite:///{PROJECT_ROOT / 'data' / 'civicforge.db'}"
    challenge_config_path: Path = PROJECT_ROOT / "config" / "challenge_config.yaml"
    cors_origins: str = "http://localhost:3000,http://127.0.0.1:3000"
    staff_api_token: str = ""
    admin_api_token: str = ""
    llm_provider: Literal["deterministic", "compatible"] = "deterministic"
    llm_base_url: str = ""
    llm_api_key: str = ""
    llm_model: str = ""
    llm_timeout_seconds: float = Field(default=8.0, ge=1, le=30)
    request_limit_per_minute: int = Field(default=120, ge=1, le=10000)
    request_max_body_bytes: int = Field(default=50000, ge=10000, le=1000000)

    @model_validator(mode="after")
    def valid_tokens(self):
        if not self.demo_mode:
            if len(self.staff_api_token) < 24 or len(self.admin_api_token) < 24:
                raise ValueError("Non-demo mode requires distinct STAFF_API_TOKEN and ADMIN_API_TOKEN of at least 24 characters.")
            if self.staff_api_token == self.admin_api_token:
                raise ValueError("Staff and administrator tokens must be distinct.")
        return self


def get_settings() -> Settings:
    return Settings()

