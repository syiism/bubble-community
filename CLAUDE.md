# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project overview

"段评气泡社区" (Paragraph Comment Bubble Community) — a web app where users create, share, and apply decorative SVG bubble styles for paragraph comments on a reading platform. Users authenticate through an external Discuz! UCenter (`vossc.com`), design SVG bubble templates with placeholder substitution (`{n}` for number, `{c}` for bubble color, `{t}` for text color), and save their current style to display when reading.

## Development commands

### Backend (Python 3.14+, FastAPI)

```bash
cd backend
uv sync           # install dependencies
uv run uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload
uv run python -m app.seed   # create DB schema + seed official bubbles (reads official_bubbles.json)
```

### Frontend (Vue 3, Vite)

```bash
cd frontend
npm install                   # uses pnpm-lock.yaml but npm works
npm run dev                   # Vite dev server on :5173, proxies /bubble-community/api to :8001
npm run build                 # output to frontend/dist/
```

### Docker (full stack)

```bash
docker compose up --build     # builds frontend → serves via FastAPI on port 8001 (external 7860 via ms_deploy)
```

The Dockerfile does a multi-stage build: Node builds the frontend, then Python runs the backend with embedded MariaDB. The entrypoint (`backend/entrypoint.sh`) waits for MySQL, runs seed, then starts uvicorn.

There are no automated tests in this repository.

## Architecture

### Backend

- **Framework**: FastAPI, all routes mounted under `/bubble-community`
- **Database**: MySQL/MariaDB via PyMySQL (`backend/app/db.py`). Context-manager `get_conn()` for connections. Schema in `backend/app/schema.sql`.
- **Config**: Environment variables (`DB_HOST`, `DB_PORT`, `DB_USER`, `DB_PASSWORD`, `DB_NAME`, `UC_KEY`) — defaults in `backend/app/config.py`.
- **Routes** (in `backend/app/routers/`):
  - `auth.py` — `POST /api/auth/login` (proxies to Discuz! UCenter login), `GET /api/auth/me`, `POST /api/auth/logout`
  - `bubbles.py` — full CRUD for bubble styles, plus `POST /visibility`, `POST /share` (generate share code), `POST /redeem` (import via share code), `POST /current` (set active bubble), `POST /favorite`
  - `user.py` — `POST /api/user/author-name` (set display name for public/shared bubbles)
- **Auth flow** (`backend/app/auth.py`): Multi-source — checks in order: (1) `user_info` dict (from login endpoint), (2) `bubble_session` cookie (DB-backed, 2-hour TTL), (3) `uc_auth` cookie (UCenter-encoded), (4) Discuz! `OcXe_*` session cookies (fetches user page to extract `discuz_uid`). On first access, auto-creates a `users` row (with auto-fetched UCenter avatar).
- **Session management** (`backend/app/session.py`): UUID-based sessions stored in `sessions` table, cookie name `bubble_session`, 2-hour expiry with sliding refresh.
- **UCenter integration** (`backend/app/ucenter.py`): Implements Discuz! `authcode` encryption/decryption for `uc_auth` cookie parsing using the `UC_KEY` secret.
- **SVG processing** (`backend/app/svg_util.py`): Normalizes various placeholder formats (`${displayText}`, `{{color}}`, etc.) to `{n}`/`{c}`/`{t}`, then fills them. The `GET /api/get-bubble` endpoint returns a fully rendered SVG for use in the reading interface.
- **Seed** (`backend/app/seed.py`): Creates database, runs schema.sql, seeds official bubbles from a JSON file (checks `user/api/bubble-style/index.html` first, falls back to `official_bubbles.json`). Idempotent — skips if official bubbles already exist.
- **Frontend serving**: In production, FastAPI mounts `frontend/dist/` as static files at `/bubble-community` with SPA fallback (all 404s serve `index.html`). In dev, Vite proxies API calls to the backend.

### Frontend

- **Stack**: Vue 3 (Composition API with `<script setup>`), Vue Router 4, Vite 8, Tailwind CSS 3
- **State management**: Reactive store pattern in `src/stores/auth.js` (no Pinia). `bootstrapAuth()` calls `/api/auth/me` on app load, `isAuthenticated` is a computed ref. The auth store exposes `login()`, `logout()`, `refreshUser()`, `getUser()`.
- **Router** (`src/router/index.js`): Three routes — `/` (Home, requires auth), `/profile` (Profile, requires auth), `/login`. Auth guard redirects to login if unauthenticated. Base path is `/bubble-community/`.
- **API layer** (`src/api.js`): Thin wrapper around `fetch()` with JSON handling, error extraction from `detail`/`message` fields, and `credentials: 'include'` for cookie auth. All endpoints under `/bubble-community/api/...`.
- **SVG utilities** (`src/utils/svgHelper.js`): Client-side counterpart of `svg_util.py` — `normalizePlaceholders()`, `fillSvg()`, `svgToImg()` (injects Tailwind classes into SVG for preview), `extractColors()` (finds hardcoded hex/RGB in SVG), `autoMapColors()` (auto-detects fill/stroke colors and converts to `{c}`/`{t}` placeholders). Duplicated logic between frontend/backend is intentional — the editor needs live preview without round-trips.
- **Key components**:
  - `BubbleCard.vue` — renders a bubble style card with preview, status badges, and owner actions (edit/share/delete/toggle-public)
  - `BubbleList.vue` — groups styles into sections (mine, favorites, imported, public, official), supports sorting by "new" or "hot"
  - `Editor.vue` — modal form for creating/editing bubbles with SVG input, color pickers, color extraction, and live preview
  - `Toast.vue` — floating notification (exposed via `ref` and `defineExpose`)
- **Component communication**: Parent (`Home.vue`) passes a `toastRef` down via props; child components emit events that Home handles, then calls `toastRef.show()` for feedback. Editor uses emit-based submit/close pattern.

### Database tables

- `users` — id (PK), username (unique), author_name (nullable unique, display name for sharing), avatar_url
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
- No ORM — raw SQL with PyMySQL `DictCursor`.
