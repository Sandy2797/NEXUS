
import json
import sqlite3
from pathlib import Path

from backend.app.schemas.event import SecurityEvent


DB_PATH = Path(__file__).resolve().parents[3] / "nexus.db"


def get_connection() -> sqlite3.Connection:
    connection = sqlite3.connect(DB_PATH, timeout=10)
    connection.row_factory = sqlite3.Row
    return connection


def initialize_database() -> None:
    with get_connection() as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS security_events (
                event_id TEXT PRIMARY KEY,
                timestamp TEXT NOT NULL,
                source TEXT NOT NULL,
                severity TEXT NOT NULL,
                finding_type TEXT NOT NULL,
                event_json TEXT NOT NULL
            )
            """
        )


def save_event(event: SecurityEvent) -> None:
    event_data = event.model_dump(mode="json")

    with get_connection() as connection:
        connection.execute(
            """
            INSERT INTO security_events (
                event_id,
                timestamp,
                source,
                severity,
                finding_type,
                event_json
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                event.event_id,
                event.timestamp.isoformat(),
                event.source,
                event.severity,
                event.finding_type,
                json.dumps(event_data),
            ),
        )


def get_event(event_id: str) -> SecurityEvent | None:
    with get_connection() as connection:
        row = connection.execute(
            """
            SELECT event_json
            FROM security_events
            WHERE event_id = ?
            """,
            (event_id,),
        ).fetchone()

    if row is None:
        return None

    return SecurityEvent.model_validate_json(row["event_json"])


def list_events(limit: int = 100) -> list[SecurityEvent]:
    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT event_json
            FROM security_events
            ORDER BY timestamp DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()

    return [
        SecurityEvent.model_validate_json(row["event_json"])
        for row in rows
    ]
