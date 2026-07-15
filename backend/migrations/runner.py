"""Migration runner — execute pending migrations in order.

Usage:
    uv run python -m migrations.runner          # apply pending
    uv run python -m migrations.runner list      # show status
"""
import os
import sys
import importlib
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

from sqlalchemy import create_engine, text, inspect
from app.config import DB_HOST, DB_PORT, DB_USER, DB_PASSWORD, DB_NAME

MIGRATIONS_TABLE = "_migrations"
ADMIN_URL = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}"
DB_URL = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}?charset=utf8mb4"


def _ensure_table(engine):
    with engine.connect() as conn:
        conn.execute(text(f"""
            CREATE TABLE IF NOT EXISTS {MIGRATIONS_TABLE} (
                name VARCHAR(255) PRIMARY KEY,
                applied_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """))
        conn.commit()


def _applied_set(engine) -> set[str]:
    with engine.connect() as conn:
        rows = conn.execute(text(f"SELECT name FROM {MIGRATIONS_TABLE}")).fetchall()
        return {r[0] for r in rows}


def _load_scripts() -> list[tuple[str, str]]:
    scripts = []
    for f in sorted(HERE.glob("[0-9]*_*.py")):
        scripts.append((f.stem, str(f)))
    return scripts


def _ensure_db_exists():
    engine = create_engine(ADMIN_URL)
    with engine.connect() as conn:
        conn.execute(text(f"CREATE DATABASE IF NOT EXISTS `{DB_NAME}` DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"))
        conn.commit()


def run(mode: str = "up"):
    _ensure_db_exists()
    engine = create_engine(DB_URL)
    _ensure_table(engine)
    applied = _applied_set(engine)
    scripts = _load_scripts()

    if mode == "list":
        for name, path in scripts:
            status = "✓" if name in applied else "—"
            print(f"  [{status}] {name}")
        return

    for name, path in _load_scripts():
        if name in applied:
            continue
        mod = importlib.import_module(f"migrations.{name}")
        print(f"  Applying {name}...", end=" ")
        mod.upgrade(engine)
        with engine.connect() as conn:
            conn.execute(text(f"INSERT INTO {MIGRATIONS_TABLE} (name) VALUES (:n)"), {"n": name})
            conn.commit()
        print("OK")

    print("All migrations applied.")


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "up"
    run(mode)
