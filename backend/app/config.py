import os
from pathlib import Path

from dotenv import load_dotenv

env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(env_path, override=True)

DB_HOST = os.getenv("DB_HOST", "127.0.0.1")
DB_PORT = int(os.getenv("DB_PORT", "3306"))
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "123456")
DB_NAME = os.getenv("DB_NAME", "bubble_community")

UC_LOGIN_URL = os.getenv("UC_LOGIN_URL", "https://vossc.com/member.php")
UC_USER_URL = os.getenv("UC_USER_URL", "https://vossc.com/home.php")
UC_AVATAR_URL = os.getenv("UC_AVATAR_URL", "https://vossc.com/uc_server/avatar.php")

REDIS_HOST = os.getenv("REDIS_HOST", "127.0.0.1")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", "")
REDIS_DB = int(os.getenv("REDIS_DB", "1"))

JWT_SECRET = os.getenv("JWT_SECRET", "cTZL7UGNklfWYwk7684PJpq1DnVp6yLxSNXogTql")
JWT_EXPIRE_DAYS = int(os.getenv("JWT_EXPIRE_DAYS", "30"))

# Cookie auth: local HTTP needs Secure=false + SameSite=Lax.
# Production HTTPS / WebView: COOKIE_SECURE=1 COOKIE_SAMESITE=none
_cookie_secure_raw = os.getenv("COOKIE_SECURE", "0").strip().lower()
COOKIE_SECURE = _cookie_secure_raw in ("1", "true", "yes", "on")
COOKIE_SAMESITE = (os.getenv("COOKIE_SAMESITE", "lax") or "lax").strip().lower()
if COOKIE_SAMESITE not in ("lax", "strict", "none"):
    COOKIE_SAMESITE = "lax"
# SameSite=None requires Secure
if COOKIE_SAMESITE == "none":
    COOKIE_SECURE = True