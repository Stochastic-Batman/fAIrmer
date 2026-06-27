import hashlib
import os
import sqlite3
from contextlib import contextmanager


DB_PATH = os.environ.get("DB_PATH", os.path.join(os.path.dirname(__file__), "..", "data", "fairmer.db"))


@contextmanager
def get_connection():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db():
    # created_at is TEXT because SQLite does not have DATETIME
    with get_connection() as conn: 
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS users (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                username      TEXT    NOT NULL UNIQUE,
                password_hash TEXT    NOT NULL,
                region        TEXT,
                primary_crops TEXT,
                soil_metrics  TEXT,
                created_at    TEXT    NOT NULL DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS chat_sessions (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id    INTEGER NOT NULL REFERENCES users(id),
                created_at TEXT    NOT NULL DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS chat_messages (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id  INTEGER NOT NULL REFERENCES chat_sessions(id),
                query_ka    TEXT    NOT NULL,
                query_en    TEXT,
                response_en TEXT,
                response_ka TEXT,
                created_at  TEXT    NOT NULL DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS alert_logs (
                id               INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id          INTEGER NOT NULL REFERENCES users(id),
                produce_category TEXT    NOT NULL,
                freshness_label  TEXT    NOT NULL,
                confidence       REAL    NOT NULL,
                advice_en        TEXT,
                advice_ka        TEXT,
                created_at       TEXT    NOT NULL DEFAULT (datetime('now'))
            );
        """)


def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


def verify_password(password: str, password_hash: str) -> bool:
    return hash_password(password) == password_hash
