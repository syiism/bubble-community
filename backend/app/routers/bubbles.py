import secrets

from fastapi import APIRouter, Body, Depends, HTTPException, status
from pydantic import BaseModel

from ..auth import get_current_user
from ..db import get_conn

router = APIRouter(prefix="/api/bubbles", tags=["bubbles"])


class BubbleCreate(BaseModel):
    name: str = ""
    desc: str = ""
    svg: str
    color: str = ""
    textColor: str = ""
    public: bool = False


class VisibilityBody(BaseModel):
    id: int
    public: bool


class ShareBody(BaseModel):
    id: int


class RedeemBody(BaseModel):
    code: str


class CurrentBody(BaseModel):
    style: int | str


class FavoriteBody(BaseModel):
    id: int
    favorite: bool


def _row_to_style(row, user_id, imported_set, favorite_set):
    mine = row["user_id"] == user_id
    return {
        "id": row["id"],
        "name": row["name"],
        "desc": row["description"],
        "svg": row["svg_template"],
        "rawSvg": row["svg_template"],
        "color": row["color"],
        "textColor": row["text_color"],
        "official": bool(row["is_official"]),
        "public": bool(row["is_public"]),
        "mine": mine,
        "imported": row["id"] in imported_set,
        "favorited": row["id"] in favorite_set,
        "uses": row["uses"],
        "author": row["author_name"] or ("" if row["is_official"] else "匿名书友"),
        "shareCode": row["share_code"] if mine else "",
    }


@router.get("")
def list_bubbles(user=Depends(get_current_user)):
    user_id = user["id"]
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT b.*,
                  (SELECT COUNT(*) FROM user_current_bubble u WHERE u.bubble_id = b.id) AS uses
                FROM bubbles b
                WHERE b.is_official = 1
                   OR b.is_public = 1
                   OR b.user_id = %s
                   OR b.id IN (SELECT bubble_id FROM imported_bubbles WHERE user_id = %s)
                ORDER BY b.is_official DESC, b.id DESC
                """,
                (user_id, user_id),
            )
            rows = cur.fetchall()
            cur.execute(
                "SELECT bubble_id FROM imported_bubbles WHERE user_id = %s",
                (user_id,),
            )
            imported_set = {r["bubble_id"] for r in cur.fetchall()}
            cur.execute(
                "SELECT bubble_id FROM user_favorites WHERE user_id = %s",
                (user_id,),
            )
            favorite_set = {r["bubble_id"] for r in cur.fetchall()}
            cur.execute(
                "SELECT bubble_id FROM user_current_bubble WHERE user_id = %s",
                (user_id,),
            )
            cur_row = cur.fetchone()
            cur.execute("SELECT author_name FROM users WHERE id = %s", (user_id,))
            urow = cur.fetchone()

    styles = [_row_to_style(r, user_id, imported_set, favorite_set) for r in rows]
    current_id = cur_row["bubble_id"] if cur_row else (styles[0]["id"] if styles else 0)
    visible_ids = {s["id"] for s in styles}
    if current_id not in visible_ids and styles:
        current_id = styles[0]["id"]

    return {
        "code": 0,
        "allowed": True,
        "canUpload": True,
        "authorName": (urow["author_name"] if urow else "") or "",
        "style": current_id,
        "favoritesCount": len(favorite_set),
        "styles": styles,
    }


@router.post("")
def create_bubble(body: BubbleCreate, user=Depends(get_current_user)):
    if not body.svg.strip():
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "请填写 SVG")
    user_id = user["id"]
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT author_name FROM users WHERE id = %s", (user_id,))
            urow = cur.fetchone()
            author_name = (urow["author_name"] if urow else "") or ""
            cur.execute(
                """
                INSERT INTO bubbles
                  (user_id, name, description, svg_template, color, text_color, is_public, is_official, author_name)
                VALUES (%s, %s, %s, %s, %s, %s, %s, 0, %s)
                """,
                (
                    user_id,
                    body.name.strip()[:64] or "未命名",
                    body.desc.strip()[:120],
                    body.svg,
                    body.color,
                    body.textColor,
                    1 if body.public else 0,
                    author_name,
                ),
            )
            conn.commit()
            new_id = cur.lastrowid
    return {"code": 0, "id": new_id}


@router.put("/{bubble_id}")
def update_bubble(bubble_id: int, body: BubbleCreate, user=Depends(get_current_user)):
    user_id = user["id"]
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT user_id FROM bubbles WHERE id = %s", (bubble_id,))
            row = cur.fetchone()
            if not row:
                raise HTTPException(status.HTTP_404_NOT_FOUND, "气泡不存在")
            if row["user_id"] != user_id:
                raise HTTPException(status.HTTP_403_FORBIDDEN, "只能编辑自己的气泡")
            cur.execute(
                """
                UPDATE bubbles SET name=%s, description=%s, svg_template=%s,
                  color=%s, text_color=%s, is_public=%s WHERE id=%s
                """,
                (
                    body.name.strip()[:64] or "未命名",
                    body.desc.strip()[:120],
                    body.svg,
                    body.color,
                    body.textColor,
                    1 if body.public else 0,
                    bubble_id,
                ),
            )
            conn.commit()
    return {"code": 0}


@router.delete("/{bubble_id}")
def delete_bubble(bubble_id: int, user=Depends(get_current_user)):
    user_id = user["id"]
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT user_id FROM bubbles WHERE id = %s", (bubble_id,))
            row = cur.fetchone()
            if not row:
                raise HTTPException(status.HTTP_404_NOT_FOUND, "气泡不存在")
            if row["user_id"] != user_id:
                raise HTTPException(status.HTTP_403_FORBIDDEN, "只能删除自己的气泡")
            cur.execute("DELETE FROM user_current_bubble WHERE bubble_id = %s", (bubble_id,))
            cur.execute("DELETE FROM imported_bubbles WHERE bubble_id = %s", (bubble_id,))
            cur.execute("DELETE FROM user_favorites WHERE bubble_id = %s", (bubble_id,))
            cur.execute("DELETE FROM bubbles WHERE id = %s", (bubble_id,))
            conn.commit()
    return {"code": 0}


@router.post("/visibility")
def set_visibility(body: VisibilityBody, user=Depends(get_current_user)):
    user_id = user["id"]
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT user_id FROM bubbles WHERE id = %s", (body.id,))
            row = cur.fetchone()
            if not row:
                raise HTTPException(status.HTTP_404_NOT_FOUND, "气泡不存在")
            if row["user_id"] != user_id:
                raise HTTPException(status.HTTP_403_FORBIDDEN, "只能修改自己的气泡")
            cur.execute(
                "UPDATE bubbles SET is_public = %s WHERE id = %s",
                (1 if body.public else 0, body.id),
            )
            conn.commit()
    return {"code": 0}


@router.post("/share")
def gen_share(body: ShareBody, user=Depends(get_current_user)):
    user_id = user["id"]
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT user_id, share_code FROM bubbles WHERE id = %s", (body.id,))
            row = cur.fetchone()
            if not row:
                raise HTTPException(status.HTTP_404_NOT_FOUND, "气泡不存在")
            if row["user_id"] != user_id:
                raise HTTPException(status.HTTP_403_FORBIDDEN, "只能分享自己的气泡")
            code = row["share_code"]
            if not code:
                for _ in range(8):
                    code = "B" + secrets.token_hex(4).upper()
                    cur.execute("SELECT id FROM bubbles WHERE share_code = %s", (code,))
                    if not cur.fetchone():
                        break
                cur.execute("UPDATE bubbles SET share_code = %s WHERE id = %s", (code, body.id))
                conn.commit()
    return {"code": 0, "shareCode": code}


@router.post("/redeem")
def redeem(body: RedeemBody, user=Depends(get_current_user)):
    code = body.code.strip().upper()
    if not code:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "请输入分享码")
    user_id = user["id"]
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT id, name, user_id FROM bubbles WHERE share_code = %s", (code,))
            row = cur.fetchone()
            if not row:
                raise HTTPException(status.HTTP_404_NOT_FOUND, "分享码无效")
            if row["user_id"] == user_id:
                raise HTTPException(status.HTTP_400_BAD_REQUEST, "这是你自己的气泡")
            cur.execute(
                "SELECT 1 FROM imported_bubbles WHERE user_id = %s AND bubble_id = %s",
                (user_id, row["id"]),
            )
            if not cur.fetchone():
                cur.execute(
                    "INSERT INTO imported_bubbles (user_id, bubble_id) VALUES (%s, %s)",
                    (user_id, row["id"]),
                )
                conn.commit()
    return {"code": 0, "id": row["id"], "name": row["name"]}


@router.post("/current")
def set_current(style: int | str = Body(..., embed=True), user=Depends(get_current_user)):
    user_id = user["id"]
    print(f"[DEBUG] set_current: user_id={user_id}, style={style!r}, type={type(style).__name__}")
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT id FROM bubbles WHERE id = %s", (style,))
            if not cur.fetchone():
                raise HTTPException(status.HTTP_404_NOT_FOUND, "气泡不存在")
            cur.execute(
                "REPLACE INTO user_current_bubble (user_id, bubble_id) VALUES (%s, %s)",
                (user_id, style),
            )
            conn.commit()
            # 验证写入是否成功
            cur.execute("SELECT bubble_id FROM user_current_bubble WHERE user_id = %s", (user_id,))
            row = cur.fetchone()
            print(f"[DEBUG] set_current: verify after write — {row}")
    return {"code": 0}


@router.post("/favorite")
def set_favorite(body: FavoriteBody, user=Depends(get_current_user)):
    user_id = user["id"]
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT id FROM bubbles WHERE id = %s", (body.id,))
            if not cur.fetchone():
                raise HTTPException(status.HTTP_404_NOT_FOUND, "气泡不存在")
            if body.favorite:
                cur.execute(
                    "INSERT IGNORE INTO user_favorites (user_id, bubble_id) VALUES (%s, %s)",
                    (user_id, body.id),
                )
            else:
                cur.execute(
                    "DELETE FROM user_favorites WHERE user_id = %s AND bubble_id = %s",
                    (user_id, body.id),
                )
            conn.commit()
    return {"code": 0}
