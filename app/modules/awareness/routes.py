"""Route for GET /api/awareness."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_session
from app.modules.awareness.schema import AwarenessResponse
from app.modules.awareness.service import get_awareness
from app.modules.risk.schema import Sex

router = APIRouter(prefix="/api", tags=["awareness"])


@router.get("/awareness", response_model=AwarenessResponse)
async def read_awareness(
    sex: Sex = Query(..., description="male or female"),
    age: int = Query(..., ge=0, le=120),
    session: AsyncSession = Depends(get_session),
) -> AwarenessResponse:
    result = await get_awareness(session, sex, age)
    if result is None:
        raise HTTPException(
            status_code=404, detail="No awareness data for that age and sex."
        )
    return result
