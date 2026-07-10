import os

from fastapi import Depends, FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException as StarletteHTTPException

from .auth import get_current_user_strict
from .modules.database import create_all_tables, get_db_context
from .modules.repositories import BubbleRepository, UserCurrentBubbleRepository
from .routers import auth, bubbles, user
from .svg_util import fill_svg

FRONTEND_DIST = os.path.join(os.path.dirname(__file__), "..", "..", "frontend", "dist")

app = FastAPI(title="段评气泡社区 API", version="1.0.0")

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


@app.on_event("startup")
def startup():
    create_all_tables()


@app.get("/bubble-community/api/health")
def health():
    return {"name": "段评气泡社区 API", "docs": "/bubble-community/docs"}


@app.get("/bubble-community/api/get-bubble")
def get_bubble(user=Depends(get_current_user_strict)):
    user_id = user["id"]

    with get_db_context() as db:
        current_bubble = UserCurrentBubbleRepository.get_by_user_id(db, user_id)
        if current_bubble:
            bubble_id = current_bubble.bubble_id
        else:
            fallback = BubbleRepository.get_official_first(db)
            if not fallback:
                raise HTTPException(status.HTTP_404_NOT_FOUND, "未设置气泡")
            bubble_id = fallback.id

        bubble = BubbleRepository.get_by_id(db, bubble_id)

    if not bubble:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "气泡不存在")

    svg = fill_svg(bubble.svg_template, color=bubble.color, text_color=bubble.text_color, n=12)
    return Response(
        content=svg,
        media_type="image/svg+xml",
        headers={
            "Cache-Control": "no-store, no-cache, must-revalidate, proxy-revalidate",
            "Pragma": "no-cache",
            "Expires": "0",
        },
    )


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
    def root_fallback():
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "前端未构建，请先执行 pnpm build")
