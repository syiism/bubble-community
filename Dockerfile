# ===== Stage 1: Build frontend =====
FROM node:22-slim AS frontend-build
WORKDIR /build
COPY frontend/package.json frontend/pnpm-lock.yaml ./
RUN npm install
COPY frontend/ ./
RUN npm run build

# ===== Stage 2: Backend runtime =====
FROM python:3.14-slim

ENV UV_PYTHON_PREFERENCE=only-system
RUN pip install --no-cache-dir uv

WORKDIR /app

# Install backend dependencies first (better layer caching)
COPY backend/pyproject.toml backend/uv.lock backend/.python-version ./backend/
WORKDIR /app/backend
RUN uv sync --frozen --no-dev

WORKDIR /app

# Copy backend source, seed data, and entrypoint
COPY backend/app/ ./backend/app/
COPY backend/entrypoint.sh ./backend/entrypoint.sh

# Copy built frontend
COPY --from=frontend-build /build/dist/ ./frontend/dist/

RUN chmod +x ./backend/entrypoint.sh

EXPOSE 8001

CMD ["./backend/entrypoint.sh"]
