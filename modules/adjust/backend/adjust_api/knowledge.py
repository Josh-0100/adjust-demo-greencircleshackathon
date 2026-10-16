import json
from datetime import date
from pathlib import Path

from .models import KnowledgeEntry

CATALOGUE_PATH = Path(__file__).resolve().parents[2] / "knowledge" / "catalogue.json"


class KnowledgeLibrary:
    def __init__(self, path: Path = CATALOGUE_PATH):
        data = json.loads(path.read_text())
        self.allowed_pages = {(publisher, url) for publisher, url in data["pages"].values()}
        self.entries = [KnowledgeEntry.model_validate(entry) for entry in data["entries"]]
        if len({entry.id for entry in self.entries}) != len(self.entries):
            raise ValueError("Knowledge IDs must be unique")

    def validated(self, today: date | None = None) -> list[KnowledgeEntry]:
        today = today or date.today()
        return [e for e in self.entries if e.verification_status == "verified"
                and (e.publisher, e.official_url) in self.allowed_pages
                and e.official_url.startswith("https://")
                and e.last_reviewed <= today <= e.review_due
                and e.content_owner and e.evidence_locator]

    def retrieve(self, scenarios: list[str], today: date | None = None):
        wanted = set(scenarios) | {"general", "referral"}
        return [e for e in self.validated(today) if wanted.intersection(e.scenarios)]

    def resolve(self, source_ids: list[str], today: date | None = None):
        index = {entry.id: entry for entry in self.validated(today)}
        if not all(id_ in index for id_ in source_ids):
            return []
        return [index[id_] for id_ in source_ids]
