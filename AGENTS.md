# AGENTS.md

段评气泡社区 — SVG bubble style creation/sharing platform.

## Dev commands

```bash
# Backend (Python 3.12+, FastAPI, async)
cd backend
uv sync
uv run python -m migrations.runner   # create DB + apply all migrations (idempotent)
uv run uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload

# Frontend (Vue 3, Vite 8, Tailwind 3)
cd frontend
pnpm install                        # uses pnpm-lock.yaml but npm works
pnpm dev                        # :5173, proxies /bubble-community/api → :8001
pnpm build                      # output → backend/dist/

# Production (gunicorn) — 先构建前端，再启动后端
cd frontend
pnpm install && pnpm build
cd ../backend
uv run gunicorn -c gunicorn.conf.py app.main:app   # :8000

# Nginx: syiism.cc.cd.conf (not committed) proxies /bubble-community/ → backend
# Static assets served directly by nginx with 1y cache
```

## Key architecture

- **Auth**: JWT + Redis (token store). Cookie name `bubble_community_token` (path=`/bubble-community/`). `get_current_user` tries **Bearer first, then cookie** (stale WebView cookies must not override a valid Bearer). Login/register return `token` in JSON; frontend keeps it in memory + `localStorage` (`bubble_community_jwt`) and sends `Authorization: Bearer` on every request. Nginx must forward `Authorization` if reverse-proxied. `get_current_user_optional` 返回 `None` 而非抛 401，用于公告等匿名友好端点.
- **Auth cookie flags** (env, defaults in `backend/app/config.py`): `COOKIE_SECURE` (default `0` for local HTTP), `COOKIE_SAMESITE` (default `lax`). Production HTTPS: `COOKIE_SECURE=1` + `COOKIE_SAMESITE=none` if cross-site cookies are needed. Bearer fallback covers in-app WebView when cookies are broken.
- **DB**: MySQL/MariaDB, SQLAlchemy 2.0 async with aiomysql. Schema auto-created via `Base.metadata.create_all()` on startup. Additive column migrations live in `backend/migrations/` and must be applied via `uv run python -m migrations.runner`. Connection pool: `pool_size=20`, `max_overflow=50`.
- **Upserts**: Use `mysql_insert(...).on_duplicate_key_update(...)` — never check-then-act.
- **All routes** mounted under `/bubble-community/` prefix.
- **Frontend builds to `backend/dist/`** — served by FastAPI as SPA static files in production.
- **CORS**: defaults to `localhost:5173/:5174`. Override via `CORS_ORIGINS` env var (comma-separated).
- **SVG placeholders**: canonical `{n}` (number), `{c}` (bubble color), `{t}` (text color). Accepts variants like `${displayText}`, `{{color}}` — normalized on save.
- **Editor preserve colors**: `Editor.vue` has a「保留原始颜色」switch. When on, paste/`@change` skips `autoMapColors` (no hex/rgba → `{c}`/`{t}` rewrite); color extract/apply UI is hidden. Session-only (not persisted); resets when opening/closing editor.
- **ImgToSvg tool** (`/img-to-svg`): converts uploaded images to pixel-style SVG. `composeSvgTemplate()` outputs raw `<svg>` only (no `<?xml?>`/`<!DOCTYPE>`). Clicking「→ 创建气泡」saves SVG to sessionStorage and navigates to `/?create-from-tool=1`. `Home.vue` detects the param, reads sessionStorage, and sets `pendingToolSvg` (defined in `toolBridge.js` shared ref). `Editor.vue` watches `pendingToolSvg`, strips XML declaration/DOCTYPE, and auto-maps `<text>` numbers → `{n}` (colors left as-is; user can manually trigger `autoMap()` via textarea blur if desired). `pendingFillN` stores the original number for copy-time substitution.
- **Admin user**: `syiism` (id=190) auto-promoted to admin by seed script.
- **Rate limiting**: login 5/min, register 3/min via slowapi.
- **Avatars**: stored in `backend/data/avatars/`, served at `/bubble-community/avatars/`. Gitignored — not committed. Existing DB records store URL path only (no filesystem path), so directory moves are transparent. Avatar URL includes upload timestamp (`?t=...`) to force browser cache refresh.
- **Bubble categories**: four categories — `original` (原创), `anime` (动漫), `classical` (古风), `other` (其他). Default is `original`. Category filter via `?category=` on `GET /bubbles` and `GET /admin/bubbles`. Official bubbles in seed JSON have pre-assigned categories. User can select category when creating/editing bubbles.
- **Home list pagination**: `GET /api/bubbles` is section-paginated — `section=public|mine|favorites|imported|all` (default `public`), `page`, `size` (default 18, max 50), `sort=new|hot`, `q`, `category`. Official bubbles are merged into `public` (`ORDER BY is_official DESC, …`). `section=all` is the user-visible union (public/official + own + favorites + imported), used when homepage has a keyword (`q`); still stacks `q` (name/author_name ILIKE) and `category`. Response: `items`, `hasMore`, `total`, `counts`, `style`, `currentBubble`. Homepage uses horizontal section tabs (公开 first) + infinite scroll; category pills are secondary filters applied to all sections; non-empty search requests `section=all` regardless of active tab.
- **Home deep-link from Profile**: `/?select=<bubbleId>&section=mine|favorites|imported` switches section, selects the bubble, and scrolls the card into view (`Home.vue` `applySelectQuery`).
- **Home infinite-scroll prefetch**: after each page load, `schedulePrefetch()` silently requests the next page into memory; `loadMore` consumes cache first (then network). BubbleList sentinel uses `rootMargin: 600px` for early trigger.
- **Announcements**: admin-only CRUD (`/api/admin/announcements`). Active announcements shown as modal popup on home page (只有 `GET /api/announcements`，不再默认请求 `/all`). 全部公告面板由侧边栏按钮按需加载 (`loadAllAnnouncements()`). 
- **Announcement confirmation**: `announcement_confirmations` 表记录 `(user_id, announcement_id)`. 用户点击"我知道了" → `POST /api/announcements/confirm` 立即写入 Redis Set `pending_confirmations` + 用户确认缓存 `cache:user:{uid}:confirmed_anns`. 后台协程 `flush_confirmations()` 每 10s 用 Lua 脚本原子取出 Redis 数据批量 `INSERT IGNORE` 到 MySQL. 未登录用户继续用 `localStorage` 关闭. `get_current_user_optional` 使公告接口支持匿名访问.
- **Online management** (admin): `GET /api/admin/online-users` scans Redis `bubble_tokens:*` to list active sessions (ID, username, IP, device, last active). Actions: kick (delete single session), block (set `is_blocked` + destroy all tokens).
- **Block system**: `is_blocked` column on `users` table. Blocked users get all tokens destroyed and are rejected on any API request with 401. Admin cannot block self. Unblock restores access (user must re-login).
- **Author signature**: `<!-- 创作者: {username} -->` is inserted into SVG after `<svg>` tag on **bubble creation** (`Editor.vue` `submit()`). Source priority: admin-transfer target → current user → `匿名书友`. `BubbleCard.vue` `copySvg()` checks for existing signature before inserting — if already present, copies as-is to avoid duplication.
- **Admin bubble author transfer**: edit dialog uses username input (not user dropdown). Debounced `GET /api/auth/check-username` validates existence; when taken returns `{ available: false, userId, authorName, username }`. `PUT /api/admin/bubbles/{id}` accepts `username` and resolves `user_id` server-side (missing user → 400). Empty username leaves owner unchanged.
- **Git history**: `.env` purged from all branches via `git filter-branch` + `git gc --prune=now`. Docker/entrypoint deployment files removed from repo.

## Redis caching

Frequently-read, infrequently-changed data is cached in Redis using cache-aside pattern with invalidation on write:

| Cache key | TTL | Invalidated by |
|-----------|-----|----------------|
| `cache:community-counts` | 60s | bubble create/delete/visibility toggle |
| `cache:admin:stats` | 60s | any bubble/user/announcement write operation |
| `cache:announcements:active` | 60s | admin announcement create/update/delete |
| `cache:user:{uid}:confirmed_anns` | 60s | user confirms announcement (`POST /api/announcements/confirm`) |
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
- `GET /` → 301 redirects to `/bubble-community/`.
- Admin/reviewer logout uses `window.location.href` (not Vue Router push) to guarantee redirect.
- Mobile card layout for bubble management (`Admin.vue`) hides 描述/署名/用户名/创建时间 columns; 署名 is shown inline below the bubble name in the mobile card via a `sm:hidden` div. Desktop table headers: 署名 (`authorName`), 用户名 (`username`).
- Mobile online-management cards (`Admin.vue`) show device type, role badge, IP, and last-active under the username (desktop table still hides 设备/最后活跃 until `lg`).
- Admin tab bar on mobile: horizontal scroll + short labels（用户/气泡/公告/在线）; full labels on `sm+`.
- `user_info:{uid}` Redis cache (TTL 1h) is cleared on logout via `invalidate_user_cache(uid)`.
- Frontend GET cache key (`frontend/src/api.js`) includes last 8 chars of JWT cookie to isolate users, preventing same-browser multi-account data mixing.
