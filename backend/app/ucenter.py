import base64
import hashlib
from typing import Optional

from fastapi import HTTPException, Request, status

from .config import UC_KEY


def _authcode(string: str, operation: str = "DECODE", key: str = "", expiry: int = 0) -> str:
    ckey_length = 4
    key = hashlib.md5(key.encode("utf-8") if key else UC_KEY.encode("utf-8")).hexdigest()
    key_a = hashlib.md5(key[:16].encode("utf-8")).hexdigest()
    key_b = hashlib.md5(key[16:].encode("utf-8")).hexdigest()

    if operation == "DECODE":
        key_c = string[:ckey_length] if ckey_length else ""
    else:
        key_c = hashlib.md5(str(hashlib.md5(str(time.time()).encode()).hexdigest()).encode()).hexdigest()[-ckey_length:] if ckey_length else ""

    cryptkey = key_a + hashlib.md5((key_a + key_c).encode("utf-8")).hexdigest()
    key_length = len(cryptkey)

    if operation == "DECODE":
        try:
            string = base64.b64decode(string[ckey_length:]).decode("utf-8")
        except Exception:
            return ""
    else:
        expiry_str = "%010d" % (expiry + int(time.time())) if expiry else "0000000000"
        string = expiry_str + hashlib.md5((string + key_b).encode("utf-8")).hexdigest()[:16] + string

    string_length = len(string)
    result = []
    box = list(range(256))
    rndkey = [ord(cryptkey[i % key_length]) for i in range(256)]

    j = 0
    for i in range(256):
        j = (j + box[i] + rndkey[i]) % 256
        box[i], box[j] = box[j], box[i]

    a = j = 0
    for i in range(string_length):
        a = (a + 1) % 256
        j = (j + box[a]) % 256
        box[a], box[j] = box[j], box[a]
        result.append(chr(ord(string[i]) ^ box[(box[a] + box[j]) % 256]))

    result_str = "".join(result)

    if operation == "DECODE":
        timestamp = int(result_str[:10])
        if timestamp != 0 and timestamp < int(time.time()):
            return ""
        if result_str[10:26] != hashlib.md5((result_str[26:] + key_b).encode("utf-8")).hexdigest()[:16]:
            return ""
        return result_str[26:]
    else:
        return key_c + base64.b64encode(result_str.encode("utf-8")).decode("utf-8").replace("=", "")


import time


def decode_uc_cookie(cookie_value: str) -> Optional[dict]:
    try:
        decoded = _authcode(cookie_value, "DECODE", UC_KEY)
        if not decoded:
            return None
        parts = decoded.split("|")
        if len(parts) >= 2:
            return {"uid": int(parts[0]), "username": parts[1]}
        return None
    except Exception:
        return None


def get_uc_user(request: Request) -> dict:
    uc_auth = request.cookies.get("uc_auth")
    if not uc_auth:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="未登录")

    user_data = decode_uc_cookie(uc_auth)
    if not user_data:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="无效的登录态")

    return {
        "id": user_data["uid"],
        "username": user_data["username"],
    }