from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import declarative_base
from config import settings

import logging

logger = logging.getLogger("cctv_platform.database")

db_url = settings.DATABASE_URL
is_postgres = "asyncpg" in db_url or "postgresql" in db_url

if is_postgres:
    try:
        import asyncpg  # check driver availability
    except (ImportError, ModuleNotFoundError) as exc:
        if not getattr(settings, "ALLOW_SQLITE_FALLBACK", False):
            raise RuntimeError(
                f"FATAL: Database configured as PostgreSQL ({db_url}), but 'asyncpg' driver is missing. "
                "Silent SQLite fallback is strictly forbidden to prevent divergence with PostGIS. "
                "Install asyncpg or explicitly set ALLOW_SQLITE_FALLBACK=True for isolated test environments."
            ) from exc
        logger.warning("asyncpg not installed; ALLOW_SQLITE_FALLBACK is enabled, falling back to SQLite.")
        db_url = "sqlite+aiosqlite:///./cctv_platform.db"

from sqlalchemy.pool import StaticPool

connect_args = {"check_same_thread": False} if "sqlite" in db_url else {}
poolclass = StaticPool if ":memory:" in db_url else None

engine = create_async_engine(
    db_url,
    echo=(settings.LOG_LEVEL == "DEBUG"),
    connect_args=connect_args,
    poolclass=poolclass,
)

async_session_maker = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

Base = declarative_base()

async def get_db():
    async with async_session_maker() as session:
        yield session
