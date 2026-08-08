from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from app.core.config import settings

# pool_recycle drops connections older than the interval so a stale one is never
# handed out (managed DBs close idle connections). We avoid pool_pre_ping here:
# the aiomysql driver's ping() signature is incompatible with SQLAlchemy's
# pre-ping call and raises on connection reuse.
engine = create_async_engine(settings.database_url, pool_recycle=3600)

SessionLocal = async_sessionmaker(engine, expire_on_commit=False)


class Base(DeclarativeBase):
    """Base class for ORM models. Define user-data tables as subclasses."""


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency yielding an async DB session per request."""
    async with SessionLocal() as session:
        yield session
