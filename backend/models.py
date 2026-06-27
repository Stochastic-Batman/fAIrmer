from database import get_connection, hash_password, verify_password


# Users
def create_user(username: str, password: str, region: str | None = None, primary_crops: str | None = None, soil_metrics: str | None = None) -> int:
    with get_connection() as conn:
        cur = conn.execute(
            """INSERT INTO users (username, password_hash, region, primary_crops, soil_metrics)
               VALUES (?, ?, ?, ?, ?)""",
            (username, hash_password(password), region, primary_crops, soil_metrics),
        )
        return cur.lastrowid


def get_user_by_username(username: str) -> dict | None:
    with get_connection() as conn:
        row = conn.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
        return dict(row) if row else None


def authenticate_user(username: str, password: str) -> dict | None:
    user = get_user_by_username(username)
    if user and verify_password(password, user["password_hash"]):
        return user
    return None


# Chat
def create_chat_session(user_id: int) -> int:
    with get_connection() as conn:
        cur = conn.execute("INSERT INTO chat_sessions (user_id) VALUES (?)", (user_id,))
        return cur.lastrowid


def add_chat_message(session_id: int, query_ka: str, query_en: str | None = None, response_en: str | None = None, response_ka: str | None = None) -> int:
    with get_connection() as conn:
        cur = conn.execute(
            """INSERT INTO chat_messages (session_id, query_ka, query_en, response_en, response_ka)
               VALUES (?, ?, ?, ?, ?)""",
            (session_id, query_ka, query_en, response_en, response_ka),
        )
        return cur.lastrowid


def get_chat_sessions(user_id: int, limit: int = 20) -> list[dict]:  # recent sessions without messages
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM chat_sessions WHERE user_id = ? ORDER BY created_at DESC LIMIT ?",
            (user_id, limit),
        ).fetchall()
        return [dict(r) for r in rows]


def get_session_messages(session_id: int) -> list[dict]:
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM chat_messages WHERE session_id = ? ORDER BY created_at ASC",
            (session_id,),
        ).fetchall()
        return [dict(r) for r in rows]


# Alert Logs
def create_alert_log(user_id: int, produce_category: str, freshness_label: str, confidence: float, advice_en: str | None = None, advice_ka: str | None = None) -> int:
    with get_connection() as conn:
        cur = conn.execute(
            """INSERT INTO alert_logs
               (user_id, produce_category, freshness_label, confidence, advice_en, advice_ka)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (user_id, produce_category, freshness_label, confidence, advice_en, advice_ka),
        )
        return cur.lastrowid


def get_alert_logs(user_id: int, limit: int = 50) -> list[dict]:
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM alert_logs WHERE user_id = ? ORDER BY created_at DESC LIMIT ?",
            (user_id, limit),
        ).fetchall()
        return [dict(r) for r in rows]
