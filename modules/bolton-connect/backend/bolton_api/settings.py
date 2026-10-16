"""Module-local configuration.

All settings are namespaced with the ``BOLTON_`` env prefix so they never clash
with the shared core or the Adjust module. The optional AI provider is
vendor-neutral (any OpenAI-compatible JSON endpoint) and defaults to a local
deterministic mode that needs no API key and no network access.
"""
from __future__ import annotations

from contextlib import contextmanager
from contextvars import ContextVar
from pathlib import Path
from typing import Iterator, Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

# bolton_api/ -> backend/ -> modules/bolton-connect/
MODULE_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = MODULE_ROOT / "data"
FRONTEND_DIR = MODULE_ROOT / "frontend"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="BOLTON_",
        env_file=str(MODULE_ROOT / ".env"),
        extra="ignore",
        case_sensitive=False,
    )

    demo_mode: bool = True
    borough: str = "Bolton"

    database_path: Path = DATA_DIR / "bolton_connect.db"
    directory_path: Path = DATA_DIR / "support_directory.json"
    demo_residents_path: Path = DATA_DIR / "demo_residents.json"
    frontend_dir: Path = FRONTEND_DIR

    # Optional, vendor-neutral LLM. Deterministic by default: no key, no network.
    llm_provider: Literal["deterministic", "compatible"] = "deterministic"
    llm_base_url: str = ""
    llm_api_key: str = ""
    llm_model: str = ""
    llm_timeout_seconds: float = Field(default=8.0, ge=1, le=30)

    request_limit_per_minute: int = Field(default=120, ge=1, le=10000)
    request_max_body_bytes: int = Field(default=60000, ge=10000, le=1000000)

    # Demonstration role tokens (not production authentication). When demo_mode
    # is on, an X-Demo-Role header selects the role; outside demo mode an adviser
    # or admin bearer token is required for staff/admin endpoints.
    adviser_api_token: str = ""
    admin_api_token: str = ""


_scoped_settings: ContextVar[Settings | None] = ContextVar("bolton_settings", default=None)


@contextmanager
def scoped_settings(settings: Settings) -> Iterator[None]:
    """Let an embedding host supply settings without changing standalone defaults.

    Context-local values also keep concurrently running host applications and
    tests from sharing credentials or database paths through process globals.
    """
    token = _scoped_settings.set(settings)
    try:
        yield
    finally:
        _scoped_settings.reset(token)


def get_settings() -> Settings:
    return _scoped_settings.get() or Settings()
