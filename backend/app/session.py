import os
import uuid
from datetime import datetime, timedelta

from .db import get_conn

SESSION_COOKIE = "bubble_session"
SESSION_EXPIRE = timedelta(hours=2)


def create_session(user_id: int, username: str) -> str:
    session_id = str(uuid.uuid4())
    expires_at = datetime.now() + SESSION_EXPIRE

    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO sessions (id, user_id, username, expires_at) VALUES (%s, %s, %s, %s)",
                (session_id, user_id, username, expires_at),
            )
            conn.commit()

    return session_id


def get_session(session_id: str) -> dict | None:
    if not session_id:
        return None

    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT user_id, username, expires_at FROM sessions WHERE id=%s",
                (session_id,),
            )
            row = cur.fetchone()

            if row and datetime.now() < row["expires_at"]:
                new_expires = datetime.now() + SESSION_EXPIRE
                cur.execute(
                    "UPDATE sessions SET expires_at=%s WHERE id=%s",
                    (new_expires, session_id),
                )
                conn.commit()
                return {"user_id": row["user_id"], "username": row["username"]}

            if row and datetime.now() >= row["expires_at"]:
                cur.execute("DELETE FROM sessions WHERE id=%s", (session_id,))
                conn.commit()

    return None


def delete_session(session_id: str):
    if session_id:
        with get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM sessions WHERE id=%s", (session_id,))
                conn.commit()


def init_sessions_table():
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS sessions (
                    id VARCHAR(36) PRIMARY KEY,
                    user_id BIGINT NOT NULL,
                    username VARCHAR(64) NOT NULL,
                    expires_at DATETIME NOT NULL,
                    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    INDEX idx_sessions_user (user_id),
                    INDEX idx_sessions_expires (expires_at)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            """)
            conn.commit()