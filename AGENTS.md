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
pnpm install                        # uses pnpm-lock.yaml but npm works
pnpm dev                        # :5173, proxies /bubble-community/api → :8001
pnpm build                      # output → backend/dist/

# Production (gunicorn)
cd backend
uv run gunicorn -c gunicorn.conf.py app.main:app   # :8000

# Nginx: syiism.cc.cd.conf (not committed) proxies /bubble-community/ → backend
# Static assets served directly by nginx with 1y cache
```

## Key architecture

- **Auth**: JWT (`bubble_community_token` cookie, path=`/bubble-community/`) + Redis (token store). NOT old DB session (`bubble_session`). `get_current_user` reads JWT from cookie, validates via Redis. Cookie renamed from `bubble_token` to avoid collision with other projects on same domain.
- **DB**: MySQL/MariaDB, SQLAlchemy 2.0 async with aiomysql. Schema auto-created via `Base.metadata.create_all()` (run by seed or on startup). Connection pool: `pool_size=20`, `max_overflow=50`.
- **Upserts**: Use `mysql_insert(...).on_duplicate_key_update(...)` — never check-then-act.
- **All routes** mounted under `/bubble-community/` prefix.
- **Frontend builds to `backend/dist/`** — served by FastAPI as SPA static files in production.
- **CORS**: defaults to `localhost:5173/:5174`. Override via `CORS_ORIGINS` env var (comma-separated).
- **SVG placeholders**: canonical `{n}` (number), `{c}` (bubble color), `{t}` (text color). Accepts variants like `${displayText}`, `{{color}}` — normalized on save.
- **Admin user**: `syiism` (id=190) auto-promoted to admin by seed script.
- **Rate limiting**: login 5/min, register 3/min via slowapi.
- **Avatars**: stored in `backend/data/avatars/`, served at `/bubble-community/avatars/`. Gitignored — not committed. Existing DB records store URL path only (no filesystem path), so directory moves are transparent.
- **Bubble categories**: three categories — `original` (原创), `anime` (动漫), `classical` (古风). Default is `original`. Category filter via `?category=` on `GET /bubbles` and `GET /admin/bubbles`. Official bubbles in seed JSON have pre-assigned categories. User can select category when creating/editing bubbles.
- **Git history**: `.env` purged from all branches via `git filter-branch` + `git gc --prune=now`. Docker/entrypoint deployment files removed from repo.

## Role system

Three roles: `admin` (管理员), `reviewer` (审核员), `user` (用户).

### Delete permission matrix

| Operation | admin | reviewer | user |
|-----------|:-----:|:--------:|:----:|
| Delete any bubble | ✓ | ✗ | ✗ |
| Delete any user | ✓ | ✗ | ✗ |
| Delete self | ✗ | ✗ | ✗ |
| Delete own bubble | ✓ | ✗ | ✓ |
| Delete other admin/reviewer | ✗ | ✗ | ✗ |

- admin can promote/demote any user to/from admin or reviewer.
- admin cannot demote self.
- Reviewer can set bubbles to **private** or **public**.
- Reviewer bubble management list shows **public** bubbles + private bubbles the reviewer has previously toggled (tracked by `visibility_modified_by` column).
- Reviewer cannot delete bubbles or users.

### Dependency

Use `require_role("admin", "reviewer")` for endpoints shared by admin and reviewer.
Use `require_admin` (alias for `require_role("admin")`) for admin-only endpoints.
Defined in `backend/app/auth.py`.

## Cache-control

All user-specific GET responses must include:
```
Cache-Control: no-store, no-cache, must-revalidate, proxy-revalidate
Pragma: no-cache
Expires: 0
Vary: Cookie
```
This prevents proxy/CDN caching from mixing one user's data with another's. The `Vary: Cookie` header tells caches to include the `Cookie` header in the cache key.

## Conventions

- camelCase ↔ snake_case mapping handled manually in route handlers and `_row_to_style()`.
- `async with get_db_context() as db:` for DB access. Use `load_only()` to avoid lazy loading issues.
- All mutations use optimistic local state updates (frontend) — no full list reload on success.
- No tests, no lint config, no formatter config, no CI workflows.
- `commit()` in repository methods expires ORM objects; use `await db.refresh(obj)` if accessed after commit.

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
| REDIS_PASSWORD | (empty) |
| REDIS_DB | 1 |

## Known quirks

- `backend/app/db.py` and `backend/app/schema.sql` are **obsolete** — ORM replaces them.
- Seed JSON source: tries `../../user/api/bubble-style/index.html` first, falls back to `backend/app/official_bubbles.json`.
- Seed is idempotent (checks existence before inserting).
- `GET /` → 301 redirects to `/bubble-community/`.
- Admin/reviewer logout uses `window.location.href` (not Vue Router push) to guarantee redirect.
- Mobile card layout for bubble management (`Admin.vue`) hides 描述/作者/创建者/创建时间 columns; creator info is shown inline below the bubble name in the mobile card via a `sm:hidden` div.
- `user_info:{uid}` Redis cache (TTL 1h) is cleared on logout via `invalidate_user_cache(uid)`.
- Frontend GET cache key (`frontend/src/api.js`) includes last 8 chars of JWT cookie to isolate users, preventing same-browser multi-account data mixing.
