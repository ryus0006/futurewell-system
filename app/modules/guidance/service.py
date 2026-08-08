"""Guidance service.

Selects lifestyle tips from the DB by trigger, then asks Gemini to rewrite them
into one warm paragraph. Only the risk band and the tip text are sent to Gemini,
never the clinical inputs, so no PII leaves the backend. If Gemini is unset,
rate-limited, or errors, a plain template built from the same tips is returned,
so the endpoint always responds.
"""

from __future__ import annotations

import httpx
from sqlalchemy import select, tuple_
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.modules.guidance.model import LifestyleTip
from app.modules.guidance.schema import GuidanceResponse
from app.modules.risk.schema import RiskLevel, RiskRequest

TIP_LIMIT = 6
GEMINI_TIMEOUT_S = 40.0

# Thresholds turning risk inputs into LIFESTYLE_TIP triggers (mmol/L, mmHg).
HIGH_SBP = 140
HIGH_TOTAL_CHOL = 5.2


def derive_triggers(req: RiskRequest) -> list[tuple[str, str]]:
    """Map inputs to (trigger_field, trigger_value) pairs the tips table keys on.

    General tips are keyed risk_category/always; condition tips use
    trigger_value 'yes'. Only triggers derivable from the request fields are
    returned.
    """
    pairs: list[tuple[str, str]] = [("risk_category", "always")]
    if req.smoking:
        pairs.append(("smoker", "yes"))
    if req.diabetes:
        pairs.append(("diabetes", "yes"))
    if req.systolic_bp >= HIGH_SBP:
        pairs.append(("high_bp", "yes"))
    if req.total_cholesterol >= HIGH_TOTAL_CHOL:
        pairs.append(("high_cholesterol", "yes"))
    return pairs


async def fetch_tips(
    session: AsyncSession, pairs: list[tuple[str, str]]
) -> list[LifestyleTip]:
    stmt = (
        select(LifestyleTip)
        .where(tuple_(LifestyleTip.trigger_field, LifestyleTip.trigger_value).in_(pairs))
        .order_by(LifestyleTip.priority)
        .limit(TIP_LIMIT)
    )
    return list((await session.execute(stmt)).scalars().all())


def fallback_summary(tips: list[LifestyleTip]) -> str:
    """Deterministic guidance when Gemini is unavailable."""
    if not tips:
        return (
            "Small, steady habits protect your heart: move most days, choose "
            "wholegrains and vegetables, and have your blood pressure and "
            "cholesterol checked at a clinic."
        )
    return "Focus on the highest-impact changes first: " + " ".join(
        tip.tip_text for tip in tips[:3]
    )


def _build_prompt(level: RiskLevel, tips: list[LifestyleTip]) -> str:
    tip_lines = "\n".join(f"- {tip.tip_text}" for tip in tips)
    return (
        "You are a warm, encouraging health coach for a Malaysian heart-health "
        "awareness app. The user's 10-year heart-risk band is "
        f"'{level}'. Rewrite the evidence-based tips below into ONE short, friendly "
        "paragraph of 3 to 4 sentences. Be specific and encouraging, not preachy. "
        "Do not give a medical diagnosis and do not invent facts beyond the tips.\n\n"
        f"Tips:\n{tip_lines}"
    )


async def _call_gemini(level: RiskLevel, tips: list[LifestyleTip]) -> str:
    url = (
        f"https://generativelanguage.googleapis.com/v1beta/models/"
        f"{settings.gemini_model}:generateContent"
    )
    payload = {"contents": [{"parts": [{"text": _build_prompt(level, tips)}]}]}
    async with httpx.AsyncClient(timeout=GEMINI_TIMEOUT_S) as client:
        response = await client.post(
            url,
            params={"key": settings.gemini_api_key},
            json=payload,
        )
        response.raise_for_status()
        data = response.json()
    return data["candidates"][0]["content"]["parts"][0]["text"].strip()


async def _try_gemini(level: RiskLevel, tips: list[LifestyleTip]) -> str | None:
    """Return a Gemini summary, or None to signal the caller to fall back."""
    if not settings.gemini_api_key or not tips:
        return None
    try:
        return await _call_gemini(level, tips)
    except Exception:
        # Any failure (network, timeout, rate limit, bad body) uses the fallback.
        return None


async def compose_guidance(
    session: AsyncSession, req: RiskRequest, level: RiskLevel
) -> GuidanceResponse:
    tips = await fetch_tips(session, derive_triggers(req))
    summary = await _try_gemini(level, tips)
    if summary is None:
        summary = fallback_summary(tips)
    return GuidanceResponse(summary=summary)
