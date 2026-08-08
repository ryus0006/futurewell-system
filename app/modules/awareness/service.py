"""Awareness service.

Reports ischaemic heart disease standing for a given age band and sex, plus the
men/women reference rows for the 41-59 band. Values come from the
cause_of_death table.

The mapping helpers are pure (no DB); get_awareness composes them around the
queries.
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.awareness.model import CauseOfDeath
from app.modules.awareness.schema import (
    AwarenessContext,
    AwarenessReferenceRow,
    AwarenessResponse,
)
from app.modules.risk.schema import Sex

CERTIFICATION = "Medically certified"
IHD_CAUSE = "Ischaemic heart diseases"
COHORT_BAND = "41-59"
SOURCE_LABEL = "Department of Statistics Malaysia (DOSM)"


def age_to_band(age: int) -> str:
    """Map an age to its band. Age 40 falls in 15-40, not 41-59."""
    if age <= 14:
        return "0-14"
    if age <= 40:
        return "15-40"
    if age <= 59:
        return "41-59"
    return "60+"


def db_sex(sex: Sex) -> str:
    return "Male" if sex == "male" else "Female"


def sex_label(sex: Sex) -> str:
    return "men" if sex == "male" else "women"


def format_age_band(band: str) -> str:
    if band.endswith("+"):
        return f"{band[:-1]} and above"
    return band.replace("-", " to ")


def rank_label(rank: int) -> str:
    return "number one" if rank == 1 else "a leading"


def one_in(share_percent: float) -> int:
    return round(100 / share_percent) if share_percent else 0


async def _fetch_ihd(
    session: AsyncSession, band: str, db_sex_value: str
) -> CauseOfDeath | None:
    stmt = select(CauseOfDeath).where(
        CauseOfDeath.age_group == band,
        CauseOfDeath.sex == db_sex_value,
        CauseOfDeath.certification == CERTIFICATION,
        CauseOfDeath.cause == IHD_CAUSE,
    )
    return (await session.execute(stmt)).scalar_one_or_none()


def _reference_row(sex: Sex, row: CauseOfDeath) -> AwarenessReferenceRow:
    share = float(row.percent_of_certification_group or 0)
    return AwarenessReferenceRow(
        group_label=f"Malaysian {sex_label(sex)}, {COHORT_BAND}",
        share_percent=share,
        one_in=one_in(share),
    )


async def get_awareness(
    session: AsyncSession, sex: Sex, age: int
) -> AwarenessResponse | None:
    """Return the awareness context for (sex, age), or None if the table has no
    IHD row for that band and sex."""
    band = age_to_band(age)
    row = await _fetch_ihd(session, band, db_sex(sex))
    if row is None:
        return None

    share = float(row.percent_of_certification_group or 0)
    context = AwarenessContext(
        sex_label=sex_label(sex),
        age_band=format_age_band(band),
        cause_label=(row.cause or "").lower(),
        share_percent=share,
        rank_label=rank_label(row.rank),
        one_in=one_in(share),
    )

    # Cohort comparison: IHD for men and women in the 41-59 band.
    male = await _fetch_ihd(session, COHORT_BAND, "Male")
    female = await _fetch_ihd(session, COHORT_BAND, "Female")
    reference_rows = [
        _reference_row(cohort_sex, cohort_row)
        for cohort_sex, cohort_row in (("male", male), ("female", female))
        if cohort_row is not None
    ]

    return AwarenessResponse(
        context=context,
        reference_rows=reference_rows,
        source_label=SOURCE_LABEL,
    )
