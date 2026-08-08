"""Response DTOs for GET /api/awareness (snake_case wire fields)."""

from pydantic import BaseModel


class AwarenessContext(BaseModel):
    sex_label: str
    age_band: str
    cause_label: str
    share_percent: float
    rank_label: str
    one_in: int


class AwarenessReferenceRow(BaseModel):
    group_label: str
    share_percent: float
    one_in: int


class AwarenessResponse(BaseModel):
    context: AwarenessContext
    reference_rows: list[AwarenessReferenceRow]
    source_label: str
