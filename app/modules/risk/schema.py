"""Request and response DTOs for POST /api/risk.

The eight-field request is the clinical input; the response carries the score
and the model that produced it.
"""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

Sex = Literal["male", "female"]
RiskLevel = Literal["low", "medium", "high"]


class RiskRequest(BaseModel):
    # Cholesterol is in mmol/L; the risk service converts to mg/dL. The positive
    # lower bounds keep the log transforms well defined.
    age: int = Field(ge=1, le=120)
    sex: Sex
    systolic_bp: int = Field(ge=1, le=240)
    total_cholesterol: float = Field(gt=0)
    hdl_cholesterol: float = Field(ge=0.3)
    smoking: bool
    diabetes: bool
    bp_treated: bool


class RiskModel(BaseModel):
    name: str
    citation: str
    caveat: str
    is_validated: bool


class RiskDetail(BaseModel):
    percent: float
    level: RiskLevel
    level_label: str
    horizon_years: int


class RiskResponse(BaseModel):
    # ``model`` is a domain field name, not the pydantic ``model_`` namespace.
    model_config = ConfigDict(protected_namespaces=())

    risk: RiskDetail
    model: RiskModel
