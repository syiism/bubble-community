import json
import os
from pathlib import Path

from sqlalchemy import create_engine, text

from .config import DB_HOST, DB_PORT, DB_USER, DB_PASSWORD, DB_NAME
from .modules.bubble import Bubble
from .modules.database import Base
from .modules.role import Role

HERE = Path(__file__).resolve().parent
SEED_JSON = HERE.parent.parent / "user" / "api" / "bubble-style" / "index.html"
SEED_JSON_FALLBACK = HERE / "official_bubbles.json"


def create_database():
    admin_engine = create_engine(f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/")
    with admin_engine.connect() as conn:
        conn.execute(text(f"CREATE DATABASE IF NOT EXISTS `{DB_NAME}` DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"))
        conn.commit()


def create_all_tables_sync():
    from .modules.database import DATABASE_URL
    sync_engine = create_engine(DATABASE_URL.replace("aiomysql", "pymysql"))
    Base.metadata.create_all(sync_engine)


def migrate_schema():
    """增量迁移：给已有表补充新字段和索引"""
    from .modules.database import DATABASE_URL
    sync_engine = create_engine(DATABASE_URL.replace("aiomysql", "pymysql"))
    with sync_engine.connect() as conn:
        result = conn.execute(
            text("SHOW COLUMNS FROM users LIKE 'password'")
        )
        if not result.fetchone():
            conn.execute(text("ALTER TABLE users ADD COLUMN password VARCHAR(255) DEFAULT NULL AFTER avatar_url"))
            conn.commit()
            print("[seed] 已添加 users.password 字段。")

        # 给 share_code 加 UNIQUE 索引（防止并发生成相同分享码）
        result = conn.execute(
            text("SHOW INDEX FROM bubbles WHERE Column_name = 'share_code' AND Non_unique = 0")
        )
        if not result.fetchone():
            conn.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS idx_bubbles_share_code ON bubbles(share_code)"))
            conn.commit()
            print("[seed] 已添加 bubbles.share_code UNIQUE 索引。")

        # role 字段
        result = conn.execute(
            text("SHOW COLUMNS FROM users LIKE 'role'")
        )
        if not result.fetchone():
            conn.execute(text("ALTER TABLE users ADD COLUMN role VARCHAR(32) NOT NULL DEFAULT 'user' AFTER password"))
            conn.commit()
            print("[seed] 已添加 users.role 字段。")

        # 灌入 roles 表
        count = conn.execute(text("SELECT COUNT(*) FROM roles")).scalar()
        if count == 0:
            conn.execute(text("INSERT INTO roles (name, description) VALUES ('user', '普通用户')"))
            conn.execute(text("INSERT INTO roles (name, description) VALUES ('admin', '管理员')"))
            conn.commit()
            print("[seed] 已灌入 roles 表（user / admin）。")

        # 设置 syiism(id=190) 为管理员
        result = conn.execute(
            text("SELECT role FROM users WHERE id = 190")
        )
        row = result.fetchone()
        if row and row[0] != "admin":
            conn.execute(text("UPDATE users SET role = 'admin' WHERE id = 190"))
            conn.commit()
            print("[seed] 已将用户 syiism(id=190) 设为管理员。")

        # sessions 表新字段：device_info, ip_address, last_seen_at（多设备支持）
        for col, col_def in [
            ("device_info", "VARCHAR(255) DEFAULT NULL AFTER username"),
            ("ip_address", "VARCHAR(45) DEFAULT NULL AFTER device_info"),
            ("last_seen_at", "DATETIME DEFAULT NULL AFTER expires_at"),
        ]:
            result = conn.execute(
                text(f"SHOW COLUMNS FROM sessions LIKE '{col}'")
            )
            if not result.fetchone():
                conn.execute(text(f"ALTER TABLE sessions ADD COLUMN {col} {col_def}"))
                conn.commit()
                print(f"[seed] 已添加 sessions.{col} 字段。")


def seed_official():
    seed_path = SEED_JSON if SEED_JSON.exists() else (SEED_JSON_FALLBACK if SEED_JSON_FALLBACK.exists() else None)
    if not seed_path:
        print("[seed] 未找到 seed JSON，跳过官方气泡灌入。")
        return
    print(f"[seed] 从 {seed_path} 加载官方气泡。")
    data = json.loads(seed_path.read_text(encoding="utf-8"))
    styles = data.get("styles", []) if isinstance(data, dict) else data

    from .modules.database import DATABASE_URL
    sync_engine = create_engine(DATABASE_URL.replace("aiomysql", "pymysql"))
    
    with sync_engine.connect() as conn:
        count = conn.execute(text("SELECT COUNT(*) FROM bubbles WHERE is_official = 1")).scalar()
        if count > 0:
            print("[seed] 官方气泡已存在，跳过灌入。")
            return

        inserted = 0
        for s in styles:
            if not s.get("official"):
                continue
            bubble = Bubble(
                name=(s.get("name") or "未命名")[:64],
                description=(s.get("desc") or "")[:120],
                svg_template=s.get("svg") or "",
                color=s.get("color") or "",
                text_color=s.get("textColor") or "",
                is_public=True,
                is_official=True,
                author_name="",
            )
            conn.add(bubble)
            inserted += 1
        conn.commit()
        print(f"[seed] 已灌入 {inserted} 个官方气泡。")


def main():
    print(f"[seed] 连接 {DB_HOST}:{DB_PORT} 用户 {DB_USER}")
    create_database()
    print(f"[seed] 数据库 {DB_NAME} 就绪。")
    create_all_tables_sync()
    print("[seed] 表结构就绪。")
    migrate_schema()
    seed_official()
    print("[seed] 完成。")


if __name__ == "__main__":
    main()