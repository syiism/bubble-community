import os

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException as StarletteHTTPException

from .auth import COOKIE_NAME, decode_token
from .db import get_conn
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

app.include_router(auth.router)
app.include_router(bubbles.router)
app.include_router(user.router)


@app.on_event("startup")
def ensure_favorites_table():
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS user_favorites (
                  user_id BIGINT NOT NULL,
                  bubble_id BIGINT NOT NULL,
                  favorited_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                  PRIMARY KEY (user_id, bubble_id)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
                """
            )
            conn.commit()


@app.get("/api/health")
def health():
    return {"name": "段评气泡社区 API", "docs": "/docs"}


@app.get("/api/get-bubble")
def get_bubble(request: Request):
    token = request.cookies.get(COOKIE_NAME)
    if not token:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "未登录")
    payload = decode_token(token)
    user_id = int(payload["sub"])

    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT bubble_id FROM user_current_bubble WHERE user_id = %s",
                (user_id,),
            )
            cur_row = cur.fetchone()
            if cur_row:
                bubble_id = cur_row["bubble_id"]
            else:
                cur.execute(
                    "SELECT id FROM bubbles WHERE is_official = 1 ORDER BY id LIMIT 1"
                )
                fallback = cur.fetchone()
                if not fallback:
                    raise HTTPException(status.HTTP_404_NOT_FOUND, "未设置气泡")
                bubble_id = fallback["id"]

            cur.execute(
                "SELECT svg_template, color, text_color FROM bubbles WHERE id = %s",
                (bubble_id,),
            )
            row = cur.fetchone()

    if not row:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "气泡不存在")

    svg = fill_svg(row["svg_template"], color=row["color"], text_color=row["text_color"], n=12)
    return Response(content=svg, media_type="image/svg+xml")


class SPAStaticFiles(StaticFiles):
    async def get_response(self, path: str, scope):
        try:
            return await super().get_response(path, scope)
        except (HTTPException, StarletteHTTPException) as ex:
            if ex.status_code == 404:
                return await super().get_response("index.html", scope)
            raise ex


if os.path.isdir(FRONTEND_DIST):
    app.mount("/", SPAStaticFiles(directory=FRONTEND_DIST, html=True), name="frontend")
else:
    @app.get("/")
    def root_fallback():
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "前端未构建，请先执行 pnpm build")
