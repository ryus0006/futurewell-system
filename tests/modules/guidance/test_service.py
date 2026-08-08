"""Unit tests for the guidance service.

Trigger derivation and the fallback are pure. compose_guidance is tested with a
fake session and a monkeypatched Gemini call, so no DB or network is used.
"""

import asyncio

from app.core.config import settings
from app.modules.guidance import service as svc
from app.modules.guidance.model import LifestyleTip
from app.modules.guidance.service import (
    compose_guidance,
    derive_triggers,
    fallback_summary,
)
from app.modules.risk.schema import RiskRequest


def _req(**overrides) -> RiskRequest:
    base = dict(
        age=53,
        sex="male",
        systolic_bp=140,
        total_cholesterol=6.2,
        hdl_cholesterol=1.1,
        smoking=True,
        diabetes=False,
        bp_treated=False,
    )
    base.update(overrides)
    return RiskRequest(**base)


def _tip(text: str, priority: int = 5) -> LifestyleTip:
    return LifestyleTip(
        trigger_field="always",
        trigger_value="always",
        category="general",
        title="tip",
        tip_text=text,
        source="src",
        priority=priority,
    )


class _FakeScalars:
    def __init__(self, rows):
        self._rows = rows

    def all(self):
        return self._rows


class _FakeResult:
    def __init__(self, rows):
        self._rows = rows

    def scalars(self):
        return _FakeScalars(self._rows)


class _FakeSession:
    def __init__(self, rows):
        self._rows = rows

    async def execute(self, _stmt):
        return _FakeResult(self._rows)


def test_derive_triggers_full():
    pairs = derive_triggers(
        _req(smoking=True, systolic_bp=145, total_cholesterol=4.0, diabetes=True)
    )
    assert ("risk_category", "always") in pairs  # general tips always included
    assert ("smoker", "yes") in pairs
    assert ("diabetes", "yes") in pairs
    assert ("high_bp", "yes") in pairs
    assert ("high_cholesterol", "yes") not in pairs  # 4.0 < 5.2 threshold


def test_derive_triggers_minimal():
    pairs = derive_triggers(
        _req(smoking=False, systolic_bp=120, total_cholesterol=4.0, diabetes=False)
    )
    assert pairs == [("risk_category", "always")]


def test_fallback_no_tips_is_generic():
    assert "heart" in fallback_summary([]).lower()


def test_fallback_with_tips_uses_tip_text():
    summary = fallback_summary([_tip("Stop smoking today."), _tip("Walk 30 minutes.")])
    assert "Stop smoking today." in summary
    assert "Walk 30 minutes." in summary


def test_compose_uses_gemini_when_available(monkeypatch):
    monkeypatch.setattr(settings, "gemini_api_key", "test-key")

    async def fake_call(_level, _tips):
        return "WARM PARAGRAPH"

    monkeypatch.setattr(svc, "_call_gemini", fake_call)
    session = _FakeSession([_tip("Stop smoking.")])
    resp = asyncio.run(compose_guidance(session, _req(), "medium"))
    assert resp.summary == "WARM PARAGRAPH"


def test_compose_falls_back_on_gemini_error(monkeypatch):
    monkeypatch.setattr(settings, "gemini_api_key", "test-key")

    async def boom(_level, _tips):
        raise RuntimeError("gemini down")

    monkeypatch.setattr(svc, "_call_gemini", boom)
    session = _FakeSession([_tip("Stop smoking today.")])
    resp = asyncio.run(compose_guidance(session, _req(), "medium"))
    assert "Stop smoking today." in resp.summary


def test_compose_falls_back_without_key(monkeypatch):
    monkeypatch.setattr(settings, "gemini_api_key", "")
    session = _FakeSession([_tip("Walk daily.")])
    resp = asyncio.run(compose_guidance(session, _req(), "low"))
    assert "Walk daily." in resp.summary
