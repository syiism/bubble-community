FROM node:22-slim AS frontend-build
WORKDIR /build
COPY frontend/package.json frontend/pnpm-lock.yaml ./
RUN npm install
COPY frontend/ ./
RUN npm run build

FROM python:3.14-slim

ENV UV_PYTHON_PREFERENCE=only-system
ENV UV_INDEX_URL=https://pypi.org/simple
RUN pip install --no-cache-dir uv

RUN apt-get update && apt-get install -y --no-install-recommends \
    mariadb-server \
    && rm -rf /var/lib/apt/lists/*

RUN mkdir -p /var/run/mysqld && chown -R mysql:mysql /var/run/mysqld
RUN mkdir -p /var/lib/mysql && chown -R mysql:mysql /var/lib/mysql

WORKDIR /app

COPY backend/pyproject.toml backend/.python-version ./backend/
WORKDIR /app/backend
RUN uv sync --no-dev

WORKDIR /app

COPY backend/app/ ./backend/app/
COPY backend/entrypoint.sh ./backend/entrypoint.sh

COPY --from=frontend-build /build/dist/ ./backend/dist/

RUN chmod +x ./backend/entrypoint.sh

EXPOSE 7860

CMD ["./backend/entrypoint.sh"]