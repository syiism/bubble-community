import json
import os
from pathlib import Path

from .config import DB_HOST, DB_PORT, DB_USER, DB_PASSWORD, DB_NAME
from .modules.database import engine, create_all_tables, get_db_context
from .modules.repositories import BubbleRepository

HERE = Path(__file__).resolve().parent
SEED_JSON = HERE.parent.parent / "user" / "api" / "bubble-style" / "index.html"
SEED_JSON_FALLBACK = HERE / "official_bubbles.json"


def create_database():
    from sqlalchemy import create_engine
    admin_engine = create_engine(f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/")
    with admin_engine.connect() as conn:
        conn.execute(f"CREATE DATABASE IF NOT EXISTS `{DB_NAME}` DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
        conn.commit()


def seed_official():
    seed_path = SEED_JSON if SEED_JSON.exists() else (SEED_JSON_FALLBACK if SEED_JSON_FALLBACK.exists() else None)
    if not seed_path:
        print("[seed] 未找到 seed JSON，跳过官方气泡灌入。")
        return
    print(f"[seed] 从 {seed_path} 加载官方气泡。")
    data = json.loads(seed_path.read_text(encoding="utf-8"))
    styles = data.get("styles", []) if isinstance(data, dict) else data

    with get_db_context() as db:
        if BubbleRepository.count_official(db) > 0:
            print("[seed] 官方气泡已存在，跳过灌入。")
            return

        inserted = 0
        for s in styles:
            if not s.get("official"):
                continue
            BubbleRepository.create_official(
                db,
                name=(s.get("name") or "未命名")[:64],
                description=(s.get("desc") or "")[:120],
                svg_template=s.get("svg") or "",
                color=s.get("color") or "",
                text_color=s.get("textColor") or "",
                author_name="",
            )
            inserted += 1
        db.commit()
        print(f"[seed] 已灌入 {inserted} 个官方气泡。")


def main():
    print(f"[seed] 连接 {DB_HOST}:{DB_PORT} 用户 {DB_USER}")
    create_database()
    print(f"[seed] 数据库 {DB_NAME} 就绪。")
    create_all_tables()
    print("[seed] 表结构就绪。")
    seed_official()
    print("[seed] 完成。")


if __name__ == "__main__":
    main()
