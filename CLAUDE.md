# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project overview

"段评气泡社区" (Paragraph Comment Bubble Community) — a web app where users create, share, and apply decorative SVG bubble styles for paragraph comments on a reading platform. Users authenticate via local accounts (password-based), design SVG bubble templates with placeholder substitution (`{n}` for number, `{c}` for bubble color, `{t}` for text color), and save their current style to display when reading.

## Development commands

### Backend (Python 3.12+, FastAPI)

```bash
cd backend
uv sync           # install dependencies
uv run uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload
uv run python -m app.seed   # create DB schema + seed official bubbles + migrate schema
```

### Frontend (Vue 3, Vite)

```bash
cd frontend
npm install                   # uses pnpm-lock.yaml but npm works
npm run dev                   # Vite dev server on :5173, proxies /bubble-community/api to :8001
npm run build                 # output to backend/dist/
```

### Docker (full stack)

```bash
docker compose up --build     # builds frontend → serves via FastAPI on port 8001 (external 7860 via ms_deploy)
```

The Dockerfile does a multi-stage build: Node builds the frontend, then Python runs the backend with embedded MariaDB. The entrypoint (`backend/entrypoint.sh`) waits for MySQL, runs seed, then starts uvicorn.

There are no automated tests in this repository.

## Architecture

### Backend

- **Framework**: FastAPI, fully asynchronous, all routes mounted under `/bubble-community`
- **Database**: MySQL/MariaDB via SQLAlchemy 2.0 ORM with aiomysql async driver (`backend/app/modules/database.py`). Async session management with connection pooling (`pool_size=20`, `max_overflow=50`).
- **Repository pattern**: Database operations encapsulated in `backend/app/modules/repositories.py` with async methods. All upsert operations use `mysql_insert` with `on_duplicate_key_update` (atomic, no check-then-act race conditions).
- **Models**: Separate model files in `backend/app/modules/` — `user.py`, `role.py`, `bubble.py`, `session_model.py`, `user_current_bubble.py`, `imported_bubble.py`, `user_favorite.py`.
- **Config**: Environment variables (`DB_HOST`, `DB_PORT`, `DB_USER`, `DB_PASSWORD`, `DB_NAME`) — defaults in `backend/app/config.py`.
- **HTTP client**: Global `httpx.AsyncClient` instances in `backend/app/http_client.py` for efficient reuse across requests.
- **Rate limiting**: `slowapi` middleware limits login (5/minute) and register (3/minute) endpoints to prevent abuse.
- **Avatar upload**: Files saved to `backend/avatars/`, served via static mount at `/bubble-community/avatars/`, URL stored in `users.avatar_url`.
- **Password hashing**: SHA-256 with random salt (`salt:hash` format) in `backend/app/password_util.py`.
- **Routes** (in `backend/app/routers/`):
  - `auth.py` — `POST /api/auth/login`, `POST /api/auth/register`, `GET /api/auth/me`, `POST /api/auth/logout`
  - `bubbles.py` — full CRUD for bubble styles, plus `POST /visibility`, `POST /share` (generate share code), `POST /redeem` (import via share code), `POST /current` (set active bubble), `POST /favorite`
  - `user.py` — `POST /api/user/author-name` (set display name), `POST /api/user/avatar` (upload avatar)
  - `admin.py` — Admin-only endpoints (require `role == "admin"`):
    - `GET /api/admin/stats` — dashboard stats
    - `GET /api/admin/users` — paginated user list with search + role filter
    - `PUT /api/admin/users/{id}/role` — promote/demote admin
    - `PUT /api/admin/users/{id}/password` — admin password reset
    - `DELETE /api/admin/users/{id}` — delete user (with cascade)
    - `POST /api/admin/users/batch-delete` — batch delete users
    - `GET /api/admin/bubbles` — paginated bubble list with search + type/status filters
    - `PUT /api/admin/bubbles/{id}` — edit any bubble (name, desc, svg, colors, public, author, userId)
    - `DELETE /api/admin/bubbles/{id}` — delete any bubble
    - `PUT /api/admin/bubbles/{id}/visibility` — toggle public/private
    - `POST /api/admin/bubbles/batch-delete` — batch delete bubbles
- **Auth flow** (`backend/app/auth.py`): Cookie-based session authentication. `get_current_user` returns user dict with `role` field. `require_admin` dependency checks for `role == "admin"`.
- **Session management** (`backend/app/session.py`): UUID-based sessions stored in `sessions` table, cookie name `bubble_session`, 2-hour expiry with sliding refresh.
- **SVG processing** (`backend/app/svg_util.py`): Normalizes various placeholder formats (`${displayText}`, `{{color}}`, etc.) to `{n}`/`{c}`/`{t}`, then fills them. `fill_svg` replaces `{n}` with number, `{c}`/`{t}` with color values (empty string when not provided).
- **Seed** (`backend/app/seed.py`): Creates database, runs SQLAlchemy model metadata to create tables, runs incremental migrations (password, role, share_code index), seeds roles table (`user`/`admin`), sets syiism(id=190) as admin, seeds official bubbles from a JSON file. Idempotent.
- **Frontend serving**: In production, FastAPI mounts `avatars/` then `frontend/dist/` as static files at `/bubble-community` with SPA fallback.

### Frontend

- **Stack**: Vue 3 (Composition API with `<script setup>`), Vue Router 4, Vite 8, Tailwind CSS 3
- **State management**: Reactive store pattern in `src/stores/auth.js` (no Pinia). `bootstrapAuth()` calls `/api/auth/me` on app load. Auth store tracks `user` object (includes `role`). Exports `isAuthenticated`, `getUser()`, `login()`, `logout()`, `refreshUser()`.
- **Router** (`src/router/index.js`): Routes — `/` (Home), `/profile` (Profile), `/login`, `/register`, `/admin` (Admin). Auth guard redirects unauthenticated to login. Admin route has `requiresAdmin: true` meta, non-admin users redirected to home. Base path `/bubble-community/`.
- **API layer** (`src/api.js`): Thin wrapper around `fetch()` with JSON handling, error extraction, and `credentials: 'include'` for cookie auth.
- **SVG utilities** (`src/utils/svgHelper.js`): Client-side counterpart of `svg_util.py` — `normalizePlaceholders()`, `fillSvg()`, `svgToImg()`, `extractColors()`, `autoMapColors()`.
- **Key components**:
  - `BubbleCard.vue` — renders a bubble style card with preview, status badges, and owner actions
  - `BubbleList.vue` — groups styles into sections (mine, favorites, imported, public, official), supports sorting
  - `Editor.vue` — modal form for creating/editing bubbles with SVG input, color pickers, color extraction, live preview, optional admin mode with author selection dropdown
  - `Navbar.vue` — responsive navigation with mobile hamburger menu, admin link visible only for `role === 'admin'`
  - `Toast.vue` — floating notification
- **Component communication**: Parent (`Home.vue`) passes a `toastRef` down via props; child components emit events that Home handles. Editor uses emit-based submit/close pattern.
- **Performance**: All mutations (save current, favorite, visibility, create, update, delete, share, redeem) use optimistic local state updates — no full list reload. Only fall back to `loadStyles()` on API error.
- **Admin pages**: `Admin.vue` — tabbed interface (user management / bubble management) with stats cards, search/filter, pagination, batch delete with checkboxes, inline bubble editing via Editor.vue.
- **Registration**: Email field is optional, not required for signup.

### Database tables

- `roles` — id (PK auto-increment), name (unique), description
- `users` — id (PK), username (unique), author_name (nullable unique), avatar_url, password, role (default "user"), created_at, updated_at
- `bubbles` — id (PK auto-increment), user_id (FK nullable), name, description, svg_template, color, text_color, is_public, is_official, share_code (unique), author_name, created_at, updated_at
- `sessions` — id (UUID PK), user_id, username, expires_at, created_at
- `user_current_bubble` — user_id (PK), bubble_id
- `imported_bubbles` — (user_id, bubble_id) composite PK
- `user_favorites` — (user_id, bubble_id) composite PK

### API data shape

The bubble list endpoint (`GET /api/bubbles`) is the core response. Each style object has: `id`, `name`, `desc`, `svg` (with placeholders resolved for current user), `rawSvg` (original template, shown in editor), `color`, `textColor`, `official`, `public`, `mine`, `imported`, `favorited`, `uses` (usage count), `author`, `shareCode` (only if the requesting user owns it).

## Key conventions

- Frontend ↔ backend field name mapping uses camelCase (frontend) ↔ snake_case (backend/DB), handled manually in route handlers and the `_row_to_style()` helper.
- SVG placeholders `{n}`, `{c}`, `{t}` are the canonical format; input accepts many variants (`${displayText}`, `{{bubbleColor}}`, etc.) which are normalized on save.
- The `rawSvg` field in API responses preserves the original user-submitted template (with placeholders) for editing; `svg` is the same after normalization.
- CORS is configured for localhost:5173/:5174 (Vite dev servers).
- SQLAlchemy ORM with async operations; use `await` for all database queries and transactions.
- Database sessions managed via context manager: `async with get_db_context() as db:`
- Avoid lazy loading issues by using `load_only()` in queries to explicitly load needed fields.
- Use `mysql_insert` with `on_duplicate_key_update` for atomic upserts (never check-then-act to avoid race conditions).
