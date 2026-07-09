#!/bin/sh
set -e

cd ./backend

echo "[entrypoint] Waiting for MySQL at ${DB_HOST:-127.0.0.1}:${DB_PORT:-3306}..."
uv run python - <<'PYEOF'
import os, time, sys, pymysql
host = os.getenv("DB_HOST", "127.0.0.1")
port = int(os.getenv("DB_PORT", "3306"))
user = os.getenv("DB_USER", "root")
password = os.getenv("DB_PASSWORD", "123456")
for i in range(60):
    try:
        pymysql.connect(host=host, port=port, user=user, password=password).close()
        print(f"[entrypoint] MySQL at {host}:{port} is ready.")
        sys.exit(0)
    except Exception:
        if i == 0:
            print(f"[entrypoint] Waiting for MySQL at {host}:{port}...")
        time.sleep(2)
print("[entrypoint] MySQL not available after 120s, exiting.")
sys.exit(1)
PYEOF

echo "[entrypoint] Running seed..."
uv run python -m app.seed

echo "[entrypoint] Starting uvicorn..."
exec uv run uvicorn app.main:app --host 0.0.0.0 --port 8001
