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

UC_KEY = os.getenv("UC_KEY", "L6r4t3X9IcL5M2n657g5t626J4F404Xb02w4vao7Pfm1C0E0Uay4tcF00dDbRdK9")

UC_LOGIN_URL = os.getenv("UC_LOGIN_URL", "https://vossc.com/member.php")
UC_USER_URL = os.getenv("UC_USER_URL", "https://vossc.com/home.php")
UC_AVATAR_URL = os.getenv("UC_AVATAR_URL", "https://vossc.com/uc_server/avatar.php")