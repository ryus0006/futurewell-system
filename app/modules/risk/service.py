"""Risk service: Framingham General CVD 10-year risk (D'Agostino 2008).

Pure calculation, no database. Inputs are not persisted. Cholesterol arrives in
mmol/L and is converted to mg/dL for the model's coefficients.

Reference: D'Agostino RB Sr, et al. General Cardiovascular Risk Profile for Use
in Primary Care: The Framingham Heart Study. Circulation. 2008;117:743-753.
"""

from __future__ import annotations

import math

from app.modules.risk.schema import (
    RiskDetail,
    RiskLevel,
    RiskModel,
    RiskRequest,
    RiskResponse,
)

MMOL_TO_MGDL = 38.67

# Sex-specific coefficients, baseline survival S0(10), and mean linear predictor.
_COEFFS = {
    "male": {
        "ln_age": 3.06117,
        "ln_total_chol": 1.12370,
        "ln_hdl": -0.93263,
        "ln_sbp_untreated": 1.93303,
        "ln_sbp_treated": 1.99881,
        "smoker": 0.65451,
        "diabetes": 0.57367,
        "s0": 0.88936,
        "mean": 23.9802,
    },
    "female": {
        "ln_age": 2.32888,
        "ln_total_chol": 1.20904,
        "ln_hdl": -0.70833,
        "ln_sbp_untreated": 2.76157,
        "ln_sbp_treated": 2.82263,
        "smoker": 0.52873,
        "diabetes": 0.69154,
        "s0": 0.95012,
        "mean": 26.1931,
    },
}

MODEL = RiskModel(
    name="Framingham General CVD Risk (D'Agostino et al., 2008)",
    citation=(
        "D'Agostino RB Sr, et al. General Cardiovascular Risk Profile for Use in "
        "Primary Care: The Framingham Heart Study. Circulation. 2008;117:743-753."
    ),
    caveat=(
        "Ten-year general cardiovascular disease risk. May not be calibrated for "
        "the Malaysian population. For awareness only, not a diagnosis."
    ),
    is_validated=True,
)

HORIZON_YEARS = 10


def _level(percent: float) -> tuple[RiskLevel, str]:
    if percent < 10:
        return "low", "Low"
    if percent < 20:
        return "medium", "Medium"
    return "high", "High"


def compute_percent(req: RiskRequest) -> float:
    """Return the 10-year CVD risk as a percentage, rounded to one decimal."""
    c = _COEFFS[req.sex]
    total_chol_mgdl = req.total_cholesterol * MMOL_TO_MGDL
    hdl_mgdl = req.hdl_cholesterol * MMOL_TO_MGDL
    sbp_beta = c["ln_sbp_treated"] if req.bp_treated else c["ln_sbp_untreated"]

    linear = (
        c["ln_age"] * math.log(req.age)
        + c["ln_total_chol"] * math.log(total_chol_mgdl)
        + c["ln_hdl"] * math.log(hdl_mgdl)
        + sbp_beta * math.log(req.systolic_bp)
        + c["smoker"] * (1 if req.smoking else 0)
        + c["diabetes"] * (1 if req.diabetes else 0)
    )

    risk = 1 - c["s0"] ** math.exp(linear - c["mean"])
    return round(risk * 100, 1)


def assess_risk(req: RiskRequest) -> RiskResponse:
    percent = compute_percent(req)
    level, level_label = _level(percent)
    return RiskResponse(
        risk=RiskDetail(
            percent=percent,
            level=level,
            level_label=level_label,
            horizon_years=HORIZON_YEARS,
        ),
        model=MODEL,
    )
