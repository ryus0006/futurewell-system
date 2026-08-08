"""Route for POST /api/risk."""

from fastapi import APIRouter

from app.modules.risk.schema import RiskRequest, RiskResponse
from app.modules.risk.service import assess_risk

router = APIRouter(prefix="/api", tags=["risk"])


@router.post("/risk", response_model=RiskResponse)
async def create_risk(request: RiskRequest) -> RiskResponse:
    return assess_risk(request)
