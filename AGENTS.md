# AGENTS.md

段评气泡社区 — SVG bubble style creation/sharing platform.

## Dev commands

```bash
# Backend (Python 3.12+, FastAPI, async)
cd backend
uv sync
uv run python -m app.seed          # create DB + tables + seed official bubbles (idempotent)
uv run uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload

# Frontend (Vue 3, Vite 8, Tailwind 3)
cd frontend
npm install                        # uses pnpm-lock.yaml but npm works
npm run dev                        # :5173, proxies /bubble-community/api → :8001
npm run build                      # output → backend/dist/

# Docker (full stack, MariaDB embedded in container)
docker compose up --build
```

## Key architecture

- **Auth**: JWT (`bubble_token` cookie) + Redis (token store). NOT old DB session (`bubble_session`). `get_current_user` reads JWT from cookie, validates via Redis.
- **DB**: MySQL/MariaDB, SQLAlchemy 2.0 async with aiomysql. Schema auto-created via `Base.metadata.create_all()` (run by seed or on startup). Connection pool: `pool_size=20`, `max_overflow=50`.
- **Upserts**: Use `mysql_insert(...).on_duplicate_key_update(...)` — never check-then-act.
- **All routes** mounted under `/bubble-community/` prefix.
- **Frontend builds to `backend/dist/`** — served by FastAPI as SPA static files in production.
- **CORS**: defaults to `localhost:5173/:5174`. Override via `CORS_ORIGINS` env var (comma-separated).
- **SVG placeholders**: canonical `{n}` (number), `{c}` (bubble color), `{t}` (text color). Accepts variants like `${displayText}`, `{{color}}` — normalized on save.
- **Admin user**: `syiism` (id=190) auto-promoted to admin by seed script.
- **Rate limiting**: login 5/min, register 3/min via slowapi.
- **Avatars**: stored in `backend/avatars/`, served at `/bubble-community/avatars/`.

## Conventions

- camelCase ↔ snake_case mapping handled manually in route handlers and `_row_to_style()`.
- `async with get_db_context() as db:` for DB access. Use `load_only()` to avoid lazy loading issues.
- All mutations use optimistic local state updates (frontend) — no full list reload on success.
- No tests, no lint config, no formatter config, no CI workflows.

## Config (env vars, defaults in `backend/app/config.py`)

| Var | Default |
|-----|---------|
| DB_HOST | 127.0.0.1 |
| DB_PORT | 3306 |
| DB_USER | root |
| DB_PASSWORD | 123456 |
| DB_NAME | bubble_community |
| JWT_SECRET | (hardcoded fallback) |
| REDIS_HOST | 127.0.0.1 |
| REDIS_PORT | 6379 |

## Known quirks

- `backend/app/db.py` and `backend/app/schema.sql` are **obsolete** — ORM replaces them.
- Seed JSON source: tries `../../user/api/bubble-style/index.html` first, falls back to `backend/app/official_bubbles.json`.
- Seed is idempotent (checks existence before inserting).
- Docker exposes port **7860** (not 8001) externally via `ms_deploy.json`.
