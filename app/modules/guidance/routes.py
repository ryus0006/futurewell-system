"""Route for POST /api/guidance."""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_session
from app.modules.guidance.schema import GuidanceRequest, GuidanceResponse
from app.modules.guidance.service import compose_guidance

router = APIRouter(prefix="/api", tags=["guidance"])


@router.post("/guidance", response_model=GuidanceResponse)
async def create_guidance(
    request: GuidanceRequest,
    session: AsyncSession = Depends(get_session),
) -> GuidanceResponse:
    return await compose_guidance(session, request.risk_inputs, request.level)
