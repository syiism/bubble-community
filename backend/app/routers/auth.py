from fastapi import APIRouter, Depends, HTTPException, Response, status
from pydantic import BaseModel, field_validator

from ..auth import (
    hash_password,
    verify_password,
    create_token,
    get_current_user,
    public_user,
    set_auth_cookie,
    clear_auth_cookie,
)
from ..db import get_conn

router = APIRouter(prefix="/api/auth", tags=["auth"])


class Credentials(BaseModel):
    username: str
    password: str

    @field_validator("username", "password")
    @classmethod
    def non_empty(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("不能为空")
        return v


@router.post("/register")
def register(body: Credentials, response: Response):
    username = body.username
    if len(username) < 2 or len(username) > 32:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "用户名需 2-32 个字符")
    if len(body.password) < 6:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "密码至少 6 位")

    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT id FROM users WHERE username=%s", (username,))
            if cur.fetchone():
                raise HTTPException(status.HTTP_409_CONFLICT, "用户名已被占用")
            cur.execute(
                "INSERT INTO users (username, password_hash) VALUES (%s, %s)",
                (username, hash_password(body.password)),
            )
            conn.commit()
            user_id = cur.lastrowid

    token = create_token(user_id, username)
    set_auth_cookie(response, token)
    return {"user": {"id": user_id, "username": username, "authorName": ""}}


@router.post("/login")
def login(body: Credentials, response: Response):
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id, username, password_hash, author_name FROM users WHERE username=%s",
                (body.username,),
            )
            row = cur.fetchone()
    if not row or not verify_password(body.password, row["password_hash"]):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "用户名或密码错误")
    token = create_token(row["id"], row["username"])
    set_auth_cookie(response, token)
    return {"user": public_user(row)}


@router.post("/logout")
def logout(response: Response):
    clear_auth_cookie(response)
    return {"code": 0}


@router.get("/me")
def me(user=Depends(get_current_user)):
    return {"user": public_user(user)}
