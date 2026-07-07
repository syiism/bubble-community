# 段评气泡社区 后端

Python 3 + FastAPI + UV + MySQL。

## 依赖

- Python 3.14（uv 管理）
- MySQL 8（本机 127.0.0.1:3306，root/123456）
- 用 `mariadb` CLI 做连接测试：`mariadb -h 127.0.0.1 -u root -p123456`

## 安装

```bash
cd backend
uv sync          # 安装依赖（fastapi/uvicorn/pymysql/pyjwt/passlib[bcrypt]/python-multipart）
```

> 说明：计划用 `mariadb` 官方 Python 连接器，但本机编译时 `/tmp` 配额不足失败，按计划回退到纯 Python 的 `pymysql`（兼容 MySQL 8，仅 `db.py` 一处 import）。连接测试仍用 `mariadb` CLI。

## 初始化数据库 + 灌入官方气泡

```bash
uv run python -m app.seed
```

会自动：建库 `bubble_community` → 建表 → 从 `../user/api/bubble-style/index.html` 读取 official 气泡入库。

## 启动

```bash
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8001
```

API 文档：http://127.0.0.1:8001/docs

## 认证方式

Cookie 认证（httponly，名为 `bubble_token`，`samesite=lax`）。

- 登录/注册成功后，后端通过 `Set-Cookie` 下发 token，前端无需也无法通过 JS 读取。
- 前端所有请求需带 `credentials: 'include'`（同源经 Vite 代理时浏览器自动携带）。
- `GET /api/auth/me` 根据 cookie 判断登录态。
- `POST /api/auth/logout` 清除 cookie。

## 主要接口

- `POST /api/auth/register`、`POST /api/auth/login`、`POST /api/auth/logout`、`GET /api/auth/me`
- `GET /api/bubbles`、`POST /api/bubbles`、`PUT /api/bubbles/{id}`、`DELETE /api/bubbles/{id}`
- `POST /api/bubbles/visibility`、`POST /api/bubbles/share`、`POST /api/bubbles/redeem`、`POST /api/bubbles/current`、`POST /api/bubbles/favorite`
- `POST /api/user/author-name`
- `GET /api/health` → 健康检查
- `GET /api/get-bubble` → `image/svg+xml`（**无需任何参数**，凭 cookie 识别当前用户，返回其选用气泡的 SVG；未登录返回 401）

## 前端静态托管

后端根路径 `/` 直接托管前端打包产物（`frontend/dist/`）。启动前需先构建前端：

```bash
cd frontend && pnpm build
```

- `/` 及任意非 API 路径（如 `/profile`、`/login`）返回 `index.html`（SPA 路由回退）
- `/assets/*` 返回 Vite 打包的 JS/CSS
- `/api/*`、`/docs` 为后端接口，优先匹配
