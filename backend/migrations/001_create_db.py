"""001: Create database if not exists."""
from sqlalchemy import create_engine, text
from app.config import DB_HOST, DB_PORT, DB_USER, DB_PASSWORD, DB_NAME


def upgrade(engine):
    engine = create_engine(f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}")
    with engine.connect() as conn:
        conn.execute(text(f"CREATE DATABASE IF NOT EXISTS `{DB_NAME}` DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"))
        conn.commit()
