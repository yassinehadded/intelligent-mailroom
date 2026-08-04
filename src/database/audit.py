from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator

from src.config import Settings, get_settings
from src.utils import get_logger


logger = get_logger(__name__)

SCHEMA = """
CREATE TABLE IF NOT EXISTS ingestion_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at TEXT NOT NULL,
    event_type TEXT NOT NULL,
    email_uid TEXT,
    message_id TEXT,
    subject TEXT,
    sender_email TEXT,
    res_id INTEGER,
    destination_serial_id INTEGER,
    doctype_id INTEGER,
    category TEXT,
    confidence REAL,
    error_message TEXT,
    details_json TEXT
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_ingestion_events_message_id_ingested
    ON ingestion_events(message_id)
    WHERE message_id IS NOT NULL AND event_type = 'ingested';
"""


class AuditRepository:
    """SQLite audit trail for ingestion events."""

    def __init__(self, settings: Settings | None = None):
        self.settings = settings or get_settings()
        self.db_path = Path(self.settings.audit_db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    def _initialize(self) -> None:
        with self._connect() as connection:
            connection.executescript(SCHEMA)
            connection.execute("DROP INDEX IF EXISTS idx_ingestion_events_message_id")
            connection.commit()

    @contextmanager
    def _connect(self) -> Iterator[sqlite3.Connection]:
        connection = sqlite3.connect(self.db_path)
        connection.row_factory = sqlite3.Row
        try:
            yield connection
        finally:
            connection.close()

    def has_message_id(self, message_id: str) -> bool:
        if not message_id:
            return False

        with self._connect() as connection:
            row = connection.execute(
                "SELECT 1 FROM ingestion_events WHERE message_id = ? AND event_type = 'ingested' LIMIT 1",
                (message_id,),
            ).fetchone()
            return row is not None

    def record_event(
        self,
        *,
        event_type: str,
        email_uid: str | None = None,
        message_id: str | None = None,
        subject: str | None = None,
        sender_email: str | None = None,
        res_id: int | None = None,
        destination_serial_id: int | None = None,
        doctype_id: int | None = None,
        category: str | None = None,
        confidence: float | None = None,
        error_message: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> int:
        created_at = datetime.now(timezone.utc).isoformat()
        details_json = json.dumps(details or {}, ensure_ascii=False)

        with self._connect() as connection:
            cursor = connection.execute(
                """
                INSERT INTO ingestion_events (
                    created_at, event_type, email_uid, message_id, subject, sender_email,
                    res_id, destination_serial_id, doctype_id, category, confidence,
                    error_message, details_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    created_at,
                    event_type,
                    email_uid,
                    message_id,
                    subject,
                    sender_email,
                    res_id,
                    destination_serial_id,
                    doctype_id,
                    category,
                    confidence,
                    error_message,
                    details_json,
                ),
            )
            connection.commit()
            return int(cursor.lastrowid)

    def list_events(self, *, limit: int = 50, event_type: str | None = None) -> list[dict[str, Any]]:
        query = "SELECT * FROM ingestion_events"
        params: list[Any] = []

        if event_type:
            query += " WHERE event_type = ?"
            params.append(event_type)

        query += " ORDER BY id DESC LIMIT ?"
        params.append(limit)

        with self._connect() as connection:
            rows = connection.execute(query, params).fetchall()

        return [self._row_to_dict(row) for row in rows]

    @staticmethod
    def _row_to_dict(row: sqlite3.Row) -> dict[str, Any]:
        data = dict(row)
        details_json = data.pop("details_json", None)
        if details_json:
            try:
                data["details"] = json.loads(details_json)
            except json.JSONDecodeError:
                data["details"] = {}
        else:
            data["details"] = {}
        return data


def get_audit_repository() -> AuditRepository:
    return AuditRepository()
