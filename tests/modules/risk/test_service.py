"""Unit tests for the Framingham risk service.

A hand-computed anchor pins the formula; monotonicity tests pin the direction
of each risk factor; band tests pin the level cutoffs.
"""

from app.modules.risk.schema import RiskRequest
from app.modules.risk.service import _level, assess_risk, compute_percent


def _req(**overrides) -> RiskRequest:
    base = dict(
        age=53,
        sex="male",
        systolic_bp=140,
        total_cholesterol=6.2,  # mmol/L
        hdl_cholesterol=1.1,  # mmol/L
        smoking=True,
        diabetes=False,
        bp_treated=False,
    )
    base.update(overrides)
    return RiskRequest(**base)


def test_known_male_profile_matches_hand_calc():
    # 53yo male smoker, SBP 140 untreated, TC 6.2 / HDL 1.1 mmol/L -> ~28.2%.
    percent = compute_percent(_req())
    assert 27.5 < percent < 29.0
    resp = assess_risk(_req())
    assert resp.risk.level == "high"
    assert resp.risk.horizon_years == 10
    assert resp.model.is_validated is True


def test_low_risk_profile():
    percent = compute_percent(
        _req(
            age=45,
            sex="female",
            systolic_bp=110,
            total_cholesterol=4.5,
            hdl_cholesterol=1.6,
            smoking=False,
        )
    )
    assert percent < 10


def test_treated_bp_increases_risk():
    assert compute_percent(_req(bp_treated=True)) > compute_percent(_req(bp_treated=False))


def test_smoking_increases_risk():
    assert compute_percent(_req(smoking=True)) > compute_percent(_req(smoking=False))


def test_diabetes_increases_risk():
    assert compute_percent(_req(diabetes=True)) > compute_percent(_req(diabetes=False))


def test_level_bands():
    assert _level(5.0)[0] == "low"
    assert _level(9.9)[0] == "low"
    assert _level(10.0)[0] == "medium"
    assert _level(19.9)[0] == "medium"
    assert _level(20.0)[0] == "high"
