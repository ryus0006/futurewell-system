from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_session

router = APIRouter(prefix="/api", tags=["health"])


@router.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "healthy"}


@router.get("/health/db")
async def db_health_check(
    session: AsyncSession = Depends(get_session),
) -> dict[str, str]:
    await session.execute(text("SELECT 1"))
    return {"status": "healthy", "database": "connected"}
