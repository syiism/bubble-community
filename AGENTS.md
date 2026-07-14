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
- **Auth cookie flags** (env, defaults in `backend/app/config.py`): `COOKIE_SECURE` (default `0` for local HTTP), `COOKIE_SAMESITE` (default `lax`). Production HTTPS/WebView: `COOKIE_SECURE=1` + `COOKIE_SAMESITE=none` (None forces Secure). Set via `set_auth_cookie` / `clear_auth_cookie` in `auth.py`.
- **DB**: MySQL/MariaDB, SQLAlchemy 2.0 async with aiomysql. Schema auto-created via `Base.metadata.create_all()` (run by seed or on startup). `create_all` does **not** add columns to existing tables — additive column migrations live in `backend/app/modules/database.py` `_COLUMN_MIGRATIONS` / `_ensure_columns()` (runs on startup). Connection pool: `pool_size=20`, `max_overflow=50`.
- **Upserts**: Use `mysql_insert(...).on_duplicate_key_update(...)` — never check-then-act.
- **All routes** mounted under `/bubble-community/` prefix.
- **Frontend builds to `backend/dist/`** — served by FastAPI as SPA static files in production.
- **CORS**: defaults to `localhost:5173/:5174`. Override via `CORS_ORIGINS` env var (comma-separated).
- **SVG placeholders**: canonical `{n}` (number), `{c}` (bubble color), `{t}` (text color). Accepts variants like `${displayText}`, `{{color}}` — normalized on save.
- **Editor preserve colors**: `Editor.vue` has a「保留原始颜色」switch. When on, paste/`@change` skips `autoMapColors` (no hex/rgba → `{c}`/`{t}` rewrite); color extract/apply UI is hidden. Session-only (not persisted); resets when opening/closing editor.
- **Admin user**: `syiism` (id=190) auto-promoted to admin by seed script.
- **Rate limiting**: login 5/min, register 3/min via slowapi.
- **Avatars**: stored in `backend/data/avatars/`, served at `/bubble-community/avatars/`. Gitignored — not committed. Existing DB records store URL path only (no filesystem path), so directory moves are transparent. Avatar URL includes upload timestamp (`?t=...`) to force browser cache refresh.
- **Bubble categories**: four categories — `original` (原创), `anime` (动漫), `classical` (古风), `other` (其他). Default is `original`. Category filter via `?category=` on `GET /bubbles` and `GET /admin/bubbles`. Official bubbles in seed JSON have pre-assigned categories. User can select category when creating/editing bubbles.
- **Home list pagination**: `GET /api/bubbles` is section-paginated — `section=public|mine|favorites|imported` (default `public`), `page`, `size` (default 18, max 50), `sort=new|hot`, `q`, `category`. Official bubbles are merged into `public` (`ORDER BY is_official DESC, …`). Response: `items`, `hasMore`, `total`, `counts`, `style`, `currentBubble`. Homepage uses horizontal section tabs (公开 first) + infinite scroll; category pills are secondary filters applied to all sections.
- **Home deep-link from Profile**: `/?select=<bubbleId>&section=mine|favorites|imported` switches section, selects the bubble, and scrolls the card into view (`Home.vue` `applySelectQuery`).
- **Announcements**: admin-only CRUD (`/api/admin/announcements`). Active announcements shown as modal popup on home page. All announcements viewable via sidebar button. Dismissed announcements stored in `localStorage`.
- **Online management** (admin): `GET /api/admin/online-users` scans Redis `bubble_tokens:*` to list active sessions (ID, username, IP, device, last active). Actions: kick (delete single session), block (set `is_blocked` + destroy all tokens).
- **Block system**: `is_blocked` column on `users` table. Blocked users get all tokens destroyed and are rejected on any API request with 401. Admin cannot block self. Unblock restores access (user must re-login).
- **Copied SVG** includes `<!-- 创作者: {username} -->` comment after `<svg>` tag for attribution.
- **Admin bubble author transfer**: edit dialog uses username input (not user dropdown). Debounced `GET /api/auth/check-username` validates existence; when taken returns `{ available: false, userId, authorName, username }`. `PUT /api/admin/bubbles/{id}` accepts `username` and resolves `user_id` server-side (missing user → 400). Empty username leaves owner unchanged.
- **Git history**: `.env` purged from all branches via `git filter-branch` + `git gc --prune=now`. Docker/entrypoint deployment files removed from repo.

## Redis caching

Frequently-read, infrequently-changed data is cached in Redis using cache-aside pattern with invalidation on write:

| Cache key | TTL | Invalidated by |
|-----------|-----|----------------|
| `cache:community-counts` | 60s | bubble create/delete/visibility toggle |
| `cache:admin:stats` | 60s | any bubble/user/announcement write operation |
| `cache:announcements:active` | 60s | admin announcement create/update/delete |
| `cache:bubbles:public-list` | 60s | *(legacy key still invalidated on write; homepage list no longer uses full-list cache)* |

**Pattern:**
```python
from app.auth import cache_get, cache_set, cache_del

# Read: check cache → miss → query DB → store
cached = await cache_get("cache:key")
if cached: return cached
data = await query_db()
await cache_set("cache:key", data, 60)
return data

# Write: update DB → delete cache
await update_db()
await cache_del("cache:key")
```

TTL is a safety fallback; cache invalidation happens immediately on write via `cache_del()`.

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
| COOKIE_SECURE | 0 (local HTTP); set 1 on HTTPS |
| COOKIE_SAMESITE | lax (local); use none on cross-site HTTPS/WebView |
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
- Mobile card layout for bubble management (`Admin.vue`) hides 描述/署名/用户名/创建时间 columns; 署名 is shown inline below the bubble name in the mobile card via a `sm:hidden` div. Desktop table headers: 署名 (`authorName`), 用户名 (`username`).
- Mobile online-management cards (`Admin.vue`) show device type, role badge, IP, and last-active under the username (desktop table still hides 设备/最后活跃 until `lg`).
- Admin tab bar on mobile: horizontal scroll + short labels（用户/气泡/公告/在线）; full labels on `sm+`.
- `user_info:{uid}` Redis cache (TTL 1h) is cleared on logout via `invalidate_user_cache(uid)`.
- Frontend GET cache key (`frontend/src/api.js`) includes last 8 chars of JWT cookie to isolate users, preventing same-browser multi-account data mixing.
