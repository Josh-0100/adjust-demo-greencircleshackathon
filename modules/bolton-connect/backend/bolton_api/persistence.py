"""Persistence for sessions, consent and adviser cases (Phase 7/8 support).

Uses the Python standard library ``sqlite3`` only — no ORM — so the module runs
standalone. Three principles are baked in:

* **Explicit consent.** A resident's session is only stored when they opt in to
  save-and-resume, and sharing with an adviser is a separate explicit consent.
  Every consent decision is written to an audit trail.
* **Right to erase.** ``delete_session`` removes the session and any case made
  from it.
* **De-identified aggregates.** ``aggregate_stats`` returns counts only and never
  returns names or free text, so the adviser dashboard's summary view cannot leak
  identifiable resident data.
"""
from __future__ import annotations

import json
import sqlite3
import uuid
from contextlib import contextmanager
from datetime import datetime, timezone
from functools import lru_cache
from pathlib import Path
from typing import Iterator

from .settings import Settings, get_settings

_SCHEMA = """
CREATE TABLE IF NOT EXISTS sessions (
    id TEXT PRIMARY KEY,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    resident_name TEXT,
    consent_save INTEGER NOT NULL DEFAULT 0,
    consent_share INTEGER NOT NULL DEFAULT 0,
    request_json TEXT,
    result_json TEXT
);
CREATE TABLE IF NOT EXISTS consent_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,
    kind TEXT NOT NULL,
    granted INTEGER NOT NULL,
    created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS cases (
    id TEXT PRIMARY KEY,
    session_id TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'new',
    assigned_to TEXT,
    summary TEXT,
    needs_review INTEGER NOT NULL DEFAULT 1,
    flags TEXT
);
CREATE TABLE IF NOT EXISTS case_notes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    case_id TEXT NOT NULL,
    author_role TEXT NOT NULL,
    note TEXT NOT NULL,
    created_at TEXT NOT NULL
);
"""


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


class Store:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as conn:
            conn.executescript(_SCHEMA)

    @contextmanager
    def _connect(self) -> Iterator[sqlite3.Connection]:
        conn = sqlite3.connect(self.path, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()

    # -- sessions ----------------------------------------------------------

    def save_session(
        self,
        *,
        resident_name: str | None,
        consent_save: bool,
        consent_share: bool,
        request: dict,
        result: dict | None,
    ) -> str:
        """Persist a session. Only called when the resident has consented."""
        session_id = uuid.uuid4().hex
        now = _now()
        with self._connect() as conn:
            conn.execute(
                "INSERT INTO sessions (id, created_at, updated_at, resident_name, consent_save, consent_share, request_json, result_json)"
                " VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    session_id,
                    now,
                    now,
                    resident_name,
                    int(consent_save),
                    int(consent_share),
                    json.dumps(request),
                    json.dumps(result) if result is not None else None,
                ),
            )
            for kind, granted in (("save", consent_save), ("share", consent_share)):
                conn.execute(
                    "INSERT INTO consent_events (session_id, kind, granted, created_at) VALUES (?, ?, ?, ?)",
                    (session_id, kind, int(granted), now),
                )
        return session_id

    def get_session(self, session_id: str) -> dict | None:
        with self._connect() as conn:
            row = conn.execute("SELECT * FROM sessions WHERE id = ?", (session_id,)).fetchone()
        return _session_to_dict(row) if row else None

    def update_session_result(self, session_id: str, result: dict) -> bool:
        with self._connect() as conn:
            cur = conn.execute(
                "UPDATE sessions SET result_json = ?, updated_at = ? WHERE id = ?",
                (json.dumps(result), _now(), session_id),
            )
        return cur.rowcount > 0

    def delete_session(self, session_id: str) -> bool:
        """Erase a session and anything derived from it (right to erase)."""
        with self._connect() as conn:
            conn.execute("DELETE FROM case_notes WHERE case_id IN (SELECT id FROM cases WHERE session_id = ?)", (session_id,))
            conn.execute("DELETE FROM cases WHERE session_id = ?", (session_id,))
            conn.execute("DELETE FROM consent_events WHERE session_id = ?", (session_id,))
            cur = conn.execute("DELETE FROM sessions WHERE id = ?", (session_id,))
        return cur.rowcount > 0

    # -- cases -------------------------------------------------------------

    def create_case(
        self,
        *,
        session_id: str | None,
        summary: str,
        needs_review: bool,
        flags: list[str] | None = None,
    ) -> str:
        case_id = uuid.uuid4().hex
        now = _now()
        with self._connect() as conn:
            conn.execute(
                "INSERT INTO cases (id, session_id, created_at, updated_at, status, assigned_to, summary, needs_review, flags)"
                " VALUES (?, ?, ?, ?, 'new', NULL, ?, ?, ?)",
                (case_id, session_id, now, now, summary, int(needs_review), json.dumps(flags or [])),
            )
        return case_id

    def list_cases(self, status: str | None = None) -> list[dict]:
        query = "SELECT * FROM cases"
        params: tuple = ()
        if status:
            query += " WHERE status = ?"
            params = (status,)
        query += " ORDER BY created_at DESC"
        with self._connect() as conn:
            rows = conn.execute(query, params).fetchall()
        return [_case_to_dict(r) for r in rows]

    def get_case(self, case_id: str) -> dict | None:
        with self._connect() as conn:
            row = conn.execute("SELECT * FROM cases WHERE id = ?", (case_id,)).fetchone()
            if not row:
                return None
            notes = conn.execute(
                "SELECT author_role, note, created_at FROM case_notes WHERE case_id = ? ORDER BY created_at",
                (case_id,),
            ).fetchall()
        case = _case_to_dict(row)
        case["notes"] = [dict(n) for n in notes]
        return case

    def update_case(self, case_id: str, *, status: str | None = None, assigned_to: str | None = None) -> bool:
        sets, params = [], []
        if status is not None:
            sets.append("status = ?")
            params.append(status)
        if assigned_to is not None:
            sets.append("assigned_to = ?")
            params.append(assigned_to)
        if not sets:
            return False
        sets.append("updated_at = ?")
        params.append(_now())
        params.append(case_id)
        with self._connect() as conn:
            cur = conn.execute(f"UPDATE cases SET {', '.join(sets)} WHERE id = ?", params)
        return cur.rowcount > 0

    def add_case_note(self, case_id: str, author_role: str, note: str) -> bool:
        with self._connect() as conn:
            exists = conn.execute("SELECT 1 FROM cases WHERE id = ?", (case_id,)).fetchone()
            if not exists:
                return False
            conn.execute(
                "INSERT INTO case_notes (case_id, author_role, note, created_at) VALUES (?, ?, ?, ?)",
                (case_id, author_role, note, _now()),
            )
        return True

    # -- de-identified aggregate (safe for the dashboard summary) ----------

    def aggregate_stats(self) -> dict:
        with self._connect() as conn:
            total = conn.execute("SELECT COUNT(*) AS n FROM cases").fetchone()["n"]
            by_status = conn.execute("SELECT status, COUNT(*) AS n FROM cases GROUP BY status").fetchall()
            needs_review = conn.execute("SELECT COUNT(*) AS n FROM cases WHERE needs_review = 1").fetchone()["n"]
            sessions = conn.execute("SELECT COUNT(*) AS n FROM sessions").fetchone()["n"]
        return {
            "total_cases": total,
            "sessions_saved": sessions,
            "cases_needing_review": needs_review,
            "by_status": {r["status"]: r["n"] for r in by_status},
        }

    def reset(self) -> None:
        with self._connect() as conn:
            for table in ("case_notes", "cases", "consent_events", "sessions"):
                conn.execute(f"DELETE FROM {table}")


def _session_to_dict(row: sqlite3.Row) -> dict:
    return {
        "id": row["id"],
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
        "resident_name": row["resident_name"],
        "consent_save": bool(row["consent_save"]),
        "consent_share": bool(row["consent_share"]),
        "request": json.loads(row["request_json"]) if row["request_json"] else None,
        "result": json.loads(row["result_json"]) if row["result_json"] else None,
    }


def _case_to_dict(row: sqlite3.Row) -> dict:
    return {
        "id": row["id"],
        "session_id": row["session_id"],
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
        "status": row["status"],
        "assigned_to": row["assigned_to"],
        "summary": row["summary"],
        "needs_review": bool(row["needs_review"]),
        "flags": json.loads(row["flags"]) if row["flags"] else [],
    }


@lru_cache(maxsize=4)
def _cached_store(path_str: str) -> Store:
    return Store(Path(path_str))


def get_store(settings: Settings | None = None) -> Store:
    settings = settings or get_settings()
    return _cached_store(str(settings.database_path))
