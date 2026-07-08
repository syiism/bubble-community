import json
import os
from pathlib import Path

from .config import DB_HOST, DB_PORT, DB_USER, DB_PASSWORD, DB_NAME
from .db import open_connection

HERE = Path(__file__).resolve().parent
SCHEMA_PATH = HERE / "schema.sql"
SEED_JSON = HERE.parent.parent / "user" / "api" / "bubble-style" / "index.html"
SEED_JSON_FALLBACK = HERE / "official_bubbles.json"


def create_database():
    conn = open_connection(database=None)
    try:
        with conn.cursor() as cur:
            cur.execute(
                f"CREATE DATABASE IF NOT EXISTS `{DB_NAME}` DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
            )
        conn.commit()
    finally:
        conn.close()


def run_schema():
    sql = SCHEMA_PATH.read_text(encoding="utf-8")
    conn = open_connection()
    try:
        with conn.cursor() as cur:
            for stmt in [s for s in sql.split(";") if s.strip()]:
                cur.execute(stmt)
        conn.commit()
    finally:
        conn.close()


def seed_official():
    seed_path = SEED_JSON if SEED_JSON.exists() else (SEED_JSON_FALLBACK if SEED_JSON_FALLBACK.exists() else None)
    if not seed_path:
        print("[seed] 未找到 seed JSON，跳过官方气泡灌入。")
        return
    print(f"[seed] 从 {seed_path} 加载官方气泡。")
    data = json.loads(seed_path.read_text(encoding="utf-8"))
    styles = data.get("styles", []) if isinstance(data, dict) else data

    conn = open_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) AS c FROM bubbles WHERE is_official = 1")
            if cur.fetchone()["c"] > 0:
                print("[seed] 官方气泡已存在，跳过灌入。")
                return

            inserted = 0
            for s in styles:
                if not s.get("official"):
                    continue
                cur.execute(
                    """
                    INSERT INTO bubbles
                      (name, description, svg_template, color, text_color, is_public, is_official, author_name)
                    VALUES (%s, %s, %s, %s, %s, 1, 1, %s)
                    """,
                    (
                        (s.get("name") or "未命名")[:64],
                        (s.get("desc") or "")[:120],
                        s.get("svg") or "",
                        s.get("color") or "",
                        s.get("textColor") or "",
                        "",
                    ),
                )
                inserted += 1
        conn.commit()
        print(f"[seed] 已灌入 {inserted} 个官方气泡。")
    finally:
        conn.close()


def main():
    print(f"[seed] 连接 {DB_HOST}:{DB_PORT} 用户 {DB_USER}")
    create_database()
    print(f"[seed] 数据库 {DB_NAME} 就绪。")
    run_schema()
    print("[seed] 表结构就绪。")
    seed_official()
    print("[seed] 完成。")


if __name__ == "__main__":
    main()
