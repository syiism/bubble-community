import re

import httpx
from fastapi import APIRouter, Depends, HTTPException, Request, Response

from ..auth import _resolve_user, get_current_user, public_user

router = APIRouter(prefix="/api/auth", tags=["auth"])

UC_LOGIN_URL = "https://vossc.com/member.php"
UC_USER_URL = "https://vossc.com/home.php"


@router.post("/login")
async def login(request: Request, response: Response):
    try:
        body = await request.json()
        username = body.get("username")
        password = body.get("password")
        questionid = body.get("questionid", 0)
        answer = body.get("answer", "")
        cookietime = body.get("cookietime", 0)

        if not username or not password:
            raise HTTPException(status_code=400, detail="用户名和密码不能为空")

        async with httpx.AsyncClient(follow_redirects=True) as client:
            login_params = {
                "mod": "logging",
                "action": "login",
                "infloat": "yes",
                "handlekey": "login",
                "inajax": "1",
                "ajaxtarget": "fwin_content_login",
            }

            login_page = await client.get(UC_LOGIN_URL, params=login_params)

            formhash_match = re.search(r'name="formhash" value="([^"]+)"', login_page.text)
            loginhash_match = re.search(r'loginhash=([A-Za-z0-9]+)', login_page.text)

            if not formhash_match or not loginhash_match:
                raise HTTPException(status_code=500, detail="无法获取登录表单信息")

            formhash = formhash_match.group(1)
            loginhash = loginhash_match.group(1)

            post_params = {
                "mod": "logging",
                "action": "login",
                "loginsubmit": "yes",
                "handlekey": "login",
                "loginhash": loginhash,
            }

            post_data = {
                "formhash": formhash,
                "referer": "forum.php",
                "loginfield": "username",
                "username": username,
                "password": password,
                "questionid": questionid,
                "answer": answer,
                "cookietime": cookietime,
            }

            login_response = await client.post(
                UC_LOGIN_URL,
                params=post_params,
                data=post_data,
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )

            if login_response.status_code != 200:
                raise HTTPException(status_code=500, detail="登录请求失败")

            discuz_cookies = [(k, v) for k, v in dict(client.cookies).items() if k.startswith("OcXe_")]

            if not discuz_cookies:
                raise HTTPException(status_code=401, detail="登录失败，请检查用户名和密码")

            user_info = None
            user_page = await client.get(UC_USER_URL, params={"mod": "space", "uid": "me"})
            uid_match = re.search(r'discuz_uid\s*=\s*[\'"](\d+)[\'"]', user_page.text)
            username_match = re.search(r'欢迎您回来，\s*([^<]+)', user_page.text)

            if uid_match:
                uid = int(uid_match.group(1))
                if uid > 0:
                    user_info = {"uid": uid}
                    if username_match:
                        user_info["username"] = username_match.group(1).strip()
                    else:
                        user_info["username"] = username

            if not user_info:
                raise HTTPException(status_code=401, detail="登录失败，请检查用户名和密码")

            from ..session import create_session, SESSION_COOKIE

            print(f"[DEBUG] Login SUCCESS: uid={user_info['uid']}, username={user_info['username']}")
            print(f"[DEBUG] Discuz! cookies from httpx: {dict(client.cookies)}")

            session_id = create_session(user_info["uid"], user_info["username"])
            print(f"[DEBUG] Created session: {session_id}")
            response.set_cookie(
                key=SESSION_COOKIE,
                value=session_id,
                path="/",
                httponly=True,
                samesite="lax",
                max_age=7200,  # 2 hours
            )

            user = _resolve_user(request, user_info)

            # Also forward vossc.com cookies for potential uc_auth fallback
            for name, value in dict(client.cookies).items():
                response.set_cookie(
                    key=name,
                    value=value,
                    path="/",
                    httponly=True,
                    samesite="lax",
                )

            return {"code": 0, "message": "登录成功", "user": public_user(user)}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"登录异常: {str(e)}")


@router.get("/me")
def me(user=Depends(get_current_user)):
    return {"user": public_user(user)}


@router.post("/logout")
def logout(request: Request, response: Response):
    from ..session import SESSION_COOKIE, delete_session
    session_id = request.cookies.get(SESSION_COOKIE)
    if session_id:
        delete_session(session_id)
    response.delete_cookie(SESSION_COOKIE, path="/")
    return {"code": 0, "message": "退出成功"}