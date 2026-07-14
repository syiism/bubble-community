import logging

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base

from app.config import DB_HOST, DB_PORT, DB_USER, DB_PASSWORD, DB_NAME

logger = logging.getLogger(__name__)

DATABASE_URL = f"mysql+aiomysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}?charset=utf8mb4"

engine = create_async_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_size=20,
    max_overflow=50,
    pool_timeout=30,
    pool_recycle=3600,
)

AsyncSessionLocal = async_sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# create_all only creates missing tables, not new columns on existing tables.
# Keep additive column migrations here (idempotent).
_COLUMN_MIGRATIONS = [
    ("users", "is_blocked", "TINYINT(1) NOT NULL DEFAULT 0"),
    ("users", "blocked_at", "DATETIME NULL"),
]


async def get_db() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        yield session


def get_db_context():
    return AsyncSessionLocal()


async def _ensure_columns(conn):
    for table, column, ddl in _COLUMN_MIGRATIONS:
        r = await conn.execute(
            text(
                "SELECT COUNT(*) FROM information_schema.COLUMNS "
                "WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = :t AND COLUMN_NAME = :c"
            ),
            {"t": table, "c": column},
        )
        exists = (r.scalar() or 0) > 0
        if not exists:
            await conn.execute(text(f"ALTER TABLE `{table}` ADD COLUMN `{column}` {ddl}"))
            logger.info("Added column %s.%s", table, column)


async def create_all_tables():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        await _ensure_columns(conn)