import os

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
from starlette.exceptions import HTTPException as StarletteHTTPException

from .http_client import client, avatar_client
from .modules.database import create_all_tables
from .routers import auth, bubbles, user, admin

FRONTEND_DIST = os.path.join(os.path.dirname(__file__), "..", "dist")

app = FastAPI(title="段评气泡社区 API", version="1.0.0")

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:5174", "http://127.0.0.1:5173", "http://127.0.0.1:5174"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/bubble-community")
app.include_router(bubbles.router, prefix="/bubble-community")
app.include_router(user.router, prefix="/bubble-community")
app.include_router(admin.router, prefix="/bubble-community")


@app.on_event("startup")
async def startup():
    await create_all_tables()


@app.on_event("shutdown")
async def shutdown():
    await client.aclose()
    await avatar_client.aclose()


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
    app.mount("/bubble-community", SPAStaticFiles(directory=FRONTEND_DIST, html=True), name="frontend")
else:
    @app.get("/bubble-community")
    async def root_fallback():
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "前端未构建，请先执行 pnpm build")