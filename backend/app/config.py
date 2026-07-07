import os

DB_HOST = os.getenv("DB_HOST", "127.0.0.1")
DB_PORT = int(os.getenv("DB_PORT", "3306"))
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "123456")
DB_NAME = os.getenv("DB_NAME", "bubble_community")

JWT_SECRET = os.getenv("JWT_SECRET", "bubble-community-dev-secret-change-me")
JWT_ALG = "HS256"
JWT_EXPIRE_DAYS = 7
