"""Request and response DTOs for POST /api/guidance.

The request reuses the risk input shape plus the risk band. The response is a
single plain-language summary.
"""

from pydantic import BaseModel

from app.modules.risk.schema import RiskLevel, RiskRequest


class GuidanceRequest(BaseModel):
    risk_inputs: RiskRequest
    level: RiskLevel


class GuidanceResponse(BaseModel):
    summary: str
