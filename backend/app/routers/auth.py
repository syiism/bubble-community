import re

import httpx
from fastapi import APIRouter, Depends, HTTPException, Request, Response

from ..auth import _resolve_user, get_current_user, public_user

router = APIRouter(prefix="/api/auth", tags=["auth"])

UC_LOGIN_URL = "https://vossc.com/member.php"
UC_USER_URL = "https://vossc.com/home.php"


@router.get("/check-username")
async def check_username(username: str):
    if not username.strip():
        raise HTTPException(status_code=400, detail="用户名不能为空")

    async with httpx.AsyncClient(follow_redirects=True) as client:
        resp = await client.get(
            "https://vossc.com/forum.php",
            params={
                "mod": "ajax",
                "inajax": "yes",
                "infloat": "register",
                "handlekey": "register",
                "ajaxmenu": "1",
                "action": "checkusername",
                "username": username,
            },
        )
        cdata = re.search(r"<!\[CDATA\[(.*?)\]\]>", resp.text, re.DOTALL)
        available = bool(cdata and cdata.group(1).strip() == "succeed")
        return {"code": 0, "available": available}


@router.post("/register")
async def register(request: Request, response: Response):
    try:
        body = await request.json()
        username = body.get("username", "").strip()
        password = body.get("password", "")
        password2 = body.get("password2", "")
        email = body.get("email", "").strip()

        if not username:
            raise HTTPException(status_code=400, detail="用户名不能为空")
        if not password:
            raise HTTPException(status_code=400, detail="密码不能为空")
        if password != password2:
            raise HTTPException(status_code=400, detail="两次输入的密码不一致")
        if len(password) < 6:
            raise HTTPException(status_code=400, detail="密码长度不能少于 6 个字符")
        if not email or "@" not in email:
            raise HTTPException(status_code=400, detail="请输入正确的邮箱地址")

        async with httpx.AsyncClient(follow_redirects=True) as client:

            # ---- Step 1: check username availability ----
            check_resp = await client.get(
                "https://vossc.com/forum.php",
                params={
                    "mod": "ajax",
                    "inajax": "yes",
                    "infloat": "register",
                    "handlekey": "register",
                    "ajaxmenu": "1",
                    "action": "checkusername",
                    "username": username,
                },
            )
            cdata = re.search(
                r"<!\[CDATA\[(.*?)\]\]>", check_resp.text, re.DOTALL
            )
            if cdata and "已注册" in cdata.group(1):
                raise HTTPException(status_code=409, detail="该用户名已注册")

            # ---- Step 2: get register formhash & randomised field IDs ----
            reg_page = await client.get(
                "https://vossc.com/member.php",
                params={"mod": "register", "inajax": "1"},
            )
            html = reg_page.text

            formhash_match = re.search(
                r'name="formhash" value="([^"]+)"', html
            )
            if not formhash_match:
                raise HTTPException(
                    status_code=500, detail="无法获取注册表单信息"
                )
            formhash = formhash_match.group(1)

            # Discuz! X5 uses randomised input IDs (name="") as anti-bot measure.
            # The POST field names must match these IDs, in the exact order they
            # appear in the HTML: username, password, confirm-password, email.
            field_ids = re.findall(
                r'<input[^>]*id="([^"]+)"[^>]*name=""[^>]*>', html
            )
            if len(field_ids) < 4:
                raise HTTPException(
                    status_code=500, detail="无法解析注册表单字段"
                )

            # ---- Step 3: submit registration ----
            post_data = {
                "regsubmit": "yes",
                "formhash": formhash,
                "referer": "https://vossc.com/",
                "activationauth": "",
                field_ids[0]: username,
                field_ids[1]: password,
                field_ids[2]: password2,
                field_ids[3]: email,
            }
            reg_resp = await client.post(
                "https://vossc.com/member.php",
                params={"mod": "register"},
                data=post_data,
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )

            # ---- Step 4: check auth cookie (Discuz! auto-logs in) ----
            auth_cookie = None
            for name, value in dict(client.cookies).items():
                if name.startswith("OcXe_") and "_auth" in name:
                    auth_cookie = (name, value)
                    break

            if not auth_cookie:
                # Try to extract Discuz! error message from response body
                err_match = re.search(
                    r"抱歉[^<]*|该用户名[^<]*|Email[^<]*|密码[^<]*",
                    reg_resp.text,
                )
                msg = err_match.group(0) if err_match else "注册失败，请稍后重试"
                raise HTTPException(status_code=400, detail=msg)

            # ---- Step 5: verify user identity and create local session ----
            user_page = await client.get(
                UC_USER_URL, params={"mod": "space", "uid": "me"}
            )
            uid_match = re.search(
                r'discuz_uid\s*=\s*[\'"](\d+)[\'"]', user_page.text
            )
            username_match = re.search(
                r"欢迎您回来，\s*([^<]+)", user_page.text
            )

            if not uid_match:
                raise HTTPException(
                    status_code=500,
                    detail="注册成功但自动登录失败，请手动登录",
                )
            uid = int(uid_match.group(1))
            resolved_username = (
                username_match.group(1).strip() if username_match else username
            )

            from ..session import create_session, SESSION_COOKIE

            session_id = create_session(uid, resolved_username)
            response.set_cookie(
                key=SESSION_COOKIE,
                value=session_id,
                path="/",
                httponly=True,
                samesite="lax",
                max_age=7200,
            )

            user = _resolve_user(request, {"uid": uid, "username": resolved_username})

            # Forward all Discuz! cookies to the browser
            for name, value in dict(client.cookies).items():
                response.set_cookie(
                    key=name,
                    value=value,
                    path="/",
                    httponly=True,
                    samesite="lax",
                )

            return {
                "code": 0,
                "message": "注册成功",
                "user": public_user(user),
            }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"注册异常: {str(e)}"
        )


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
def me(user=Depends(get_current_user), response: Response = None):
    # 禁止缓存，避免浏览器返回过期的用户信息
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, proxy-revalidate"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return {"user": public_user(user)}


@router.post("/logout")
def logout(request: Request, response: Response):
    from ..session import SESSION_COOKIE, delete_session
    session_id = request.cookies.get(SESSION_COOKIE)
    if session_id:
        delete_session(session_id)
    response.delete_cookie(SESSION_COOKIE, path="/")
    # 清除所有 Discuz! 相关 cookie，避免旧 cookie 导致静默切换用户
    for name in list(request.cookies.keys()):
        if name == "uc_auth" or name.startswith("OcXe_"):
            response.delete_cookie(name, path="/")
    return {"code": 0, "message": "退出成功"}