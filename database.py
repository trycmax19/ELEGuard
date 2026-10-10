
import sqlite3
from datetime import datetime
from pathlib import Path

import pandas as pd

from config import DATABASE_PATH


def get_connection():
    Path(DATABASE_PATH).parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(
        str(DATABASE_PATH),
        timeout=10,
    )
    connection.row_factory = sqlite3.Row
    return connection


def init_db():
    with get_connection() as connection:
        connection.execute("""
            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                event_type TEXT NOT NULL,
                count INTEGER NOT NULL DEFAULT 0,
                confidence REAL NOT NULL DEFAULT 0,
                source TEXT NOT NULL,
                acknowledged INTEGER NOT NULL DEFAULT 0
            )
        """)
        connection.commit()


def log_event(event_type, count=0, confidence=0.0,
              source="webcam"):
    timestamp = datetime.now().astimezone().isoformat(
        timespec="seconds"
    )

    with get_connection() as connection:
        cursor = connection.execute(
            """
            INSERT INTO events
            (timestamp, event_type, count, confidence, source)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                timestamp,
                event_type,
                int(count),
                float(confidence),
                source,
            ),
        )
        connection.commit()
        return cursor.lastrowid


def get_events(limit=5000):
    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT id, timestamp, event_type, count,
                   confidence, source, acknowledged
            FROM events
            ORDER BY id DESC
            LIMIT ?
            """,
            (int(limit),),
        ).fetchall()

    return pd.DataFrame([dict(row) for row in rows])


def acknowledge_event(event_id):
    with get_connection() as connection:
        connection.execute(
            "UPDATE events SET acknowledged = 1 WHERE id = ?",
            (int(event_id),),
        )
        connection.commit()


def export_events_csv():
    return get_events(limit=100000).to_csv(index=False).encode("utf-8-sig")
