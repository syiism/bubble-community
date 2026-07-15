import asyncio
import logging
import os

# 配置日志：输出到 stderr，包含时间戳和模块名
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    datefmt="%H:%M:%S",
)
# 降低 SQLAlchemy 日志噪音
logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
from starlette.exceptions import HTTPException as StarletteHTTPException

from .http_client import client, avatar_client
from .modules.database import create_all_tables
from .redis_client import init_redis, close_redis
from .routers import auth, bubbles, user, admin, announcement
from .tasks import flush_confirmations

FRONTEND_DIST = os.path.join(os.path.dirname(__file__), "..", "dist")

app = FastAPI(title="段评气泡社区 API", version="1.0.0")

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS origins: 可通过环境变量 CORS_ORIGINS 配置多个（逗号分隔）
_cors_env = os.getenv("CORS_ORIGINS", "")
_cors_origins = (
    [o.strip() for o in _cors_env.split(",") if o.strip()]
    if _cors_env
    else ["http://localhost:5173", "http://localhost:5174", "http://127.0.0.1:5173", "http://127.0.0.1:5174"]
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/bubble-community")
app.include_router(bubbles.router, prefix="/bubble-community")
app.include_router(user.router, prefix="/bubble-community")
app.include_router(admin.router, prefix="/bubble-community")
app.include_router(announcement.router, prefix="/bubble-community")


_flush_task = None

@app.on_event("startup")
async def startup():
    await create_all_tables()
    await init_redis()
    global _flush_task
    _flush_task = asyncio.create_task(flush_confirmations())
    logging.getLogger("tasks").info("Background flush_confirmations task started")


@app.on_event("shutdown")
async def shutdown():
    if _flush_task:
        _flush_task.cancel()
        try:
            await _flush_task
        except asyncio.CancelledError:
            pass
    await client.aclose()
    await avatar_client.aclose()
    await close_redis()


@app.get("/")
async def root_redirect():
    return RedirectResponse(url="/bubble-community/")


@app.get("/bubble-community/health")
async def health():
    return {"name": "段评气泡社区 API", "docs": "/bubble-community/docs"}

class SPAStaticFiles(StaticFiles):
    async def get_response(self, path: str, scope):
        try:
            return await super().get_response(path, scope)
        except (HTTPException, StarletteHTTPException) as ex:
            if ex.status_code == 404:
                return await super().get_response("index.html", scope)
            raise ex


if os.path.isdir(FRONTEND_DIST):
    # 头像目录优先挂载，避免被 SPA 兜底拦截
    AVATAR_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "avatars")
    os.makedirs(AVATAR_DIR, exist_ok=True)
    app.mount("/bubble-community/avatars", StaticFiles(directory=AVATAR_DIR), name="avatars")
    app.mount("/bubble-community", SPAStaticFiles(directory=FRONTEND_DIST, html=True), name="frontend")
else:
    @app.get("/bubble-community")
    async def root_fallback():
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "前端未构建，请先执行 pnpm build")