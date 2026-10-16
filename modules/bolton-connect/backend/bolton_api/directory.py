"""Support directory loader (Phase 4).

Reads the curated ``support_directory.json`` into validated ``SupportService``
models. The directory mixes attributed real signposting services with clearly
labelled synthetic demonstration data; the ``auto_recommendable`` rule on each
service (active + verified/source_listed) is what keeps unverified, expired or
historical programmes out of automatic recommendations.
"""
from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

from pydantic import ValidationError

from .schemas import SupportCategory, SupportService
from .settings import Settings, get_settings


class Directory:
    """An in-memory, validated view of the support directory."""

    def __init__(self, services: list[SupportService], notice: str = "") -> None:
        self._services = services
        self.notice = notice
        self._by_id = {service.id: service for service in services}

    def all(self) -> list[SupportService]:
        return list(self._services)

    def get(self, service_id: str) -> SupportService | None:
        return self._by_id.get(service_id)

    def by_category(self, category: SupportCategory) -> list[SupportService]:
        return [s for s in self._services if s.category == category]

    def auto_recommendable(self) -> list[SupportService]:
        return [s for s in self._services if s.auto_recommendable]

    def categories(self) -> set[str]:
        return {s.category for s in self._services}

    def __len__(self) -> int:
        return len(self._services)


def _load_from_path(path: Path) -> Directory:
    raw = json.loads(path.read_text(encoding="utf-8"))
    services: list[SupportService] = []
    skipped: list[str] = []
    for entry in raw.get("services", []):
        try:
            services.append(SupportService.model_validate(entry))
        except ValidationError:
            # A malformed entry is skipped rather than crashing the directory;
            # better to surface fewer services than to invent or mangle one.
            skipped.append(str(entry.get("id", "<unknown>")))
    notice = raw.get("notice", "")
    if skipped:
        notice = (notice + " ").strip() + f"(Skipped {len(skipped)} malformed entr{'y' if len(skipped) == 1 else 'ies'}.)"
    return Directory(services, notice=notice)


@lru_cache(maxsize=4)
def _cached(path_str: str) -> Directory:
    return _load_from_path(Path(path_str))


def load_directory(settings: Settings | None = None) -> Directory:
    """Return the cached directory for the configured path."""
    settings = settings or get_settings()
    return _cached(str(settings.directory_path))
