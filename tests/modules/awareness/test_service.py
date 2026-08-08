"""Unit tests for the awareness service.

The pure helpers are tested directly. get_awareness is tested with a fake
session that returns canned CAUSE_OF_DEATH rows, so no MySQL is required.
"""

import asyncio
from decimal import Decimal

from app.modules.awareness.model import CauseOfDeath
from app.modules.awareness.service import (
    age_to_band,
    db_sex,
    format_age_band,
    get_awareness,
    one_in,
    rank_label,
    sex_label,
)


def test_age_to_band_boundaries():
    assert age_to_band(10) == "0-14"
    assert age_to_band(14) == "0-14"
    assert age_to_band(15) == "15-40"
    assert age_to_band(40) == "15-40"  # 40 is 15-40, not 41-59
    assert age_to_band(41) == "41-59"
    assert age_to_band(53) == "41-59"
    assert age_to_band(59) == "41-59"
    assert age_to_band(60) == "60+"


def test_one_in_matches_dosm():
    assert one_in(24.8) == 4  # male 41-59
    assert one_in(10.2) == 10  # female 41-59
    assert one_in(0) == 0  # guard against divide-by-zero


def test_rank_label():
    assert rank_label(1) == "number one"
    assert rank_label(2) == "a leading"


def test_labels_and_formatting():
    assert sex_label("male") == "men"
    assert sex_label("female") == "women"
    assert db_sex("male") == "Male"
    assert db_sex("female") == "Female"
    assert format_age_band("41-59") == "41 to 59"
    assert format_age_band("60+") == "60 and above"


class _FakeResult:
    def __init__(self, obj):
        self._obj = obj

    def scalar_one_or_none(self):
        return self._obj


class _FakeSession:
    """Returns the pre-seeded rows in call order (context, male, female)."""

    def __init__(self, rows):
        self._rows = rows
        self.calls = 0

    async def execute(self, _stmt):
        row = self._rows[self.calls]
        self.calls += 1
        return _FakeResult(row)


def _ihd_row(sex: str, pct: str, rank: int = 1) -> CauseOfDeath:
    return CauseOfDeath(
        year=2023,
        age_group="41-59",
        sex=sex,
        certification="Medically certified",
        rank=rank,
        cause="Ischaemic heart diseases",
        percent_of_certification_group=Decimal(pct),
    )


def test_get_awareness_composes_response():
    male = _ihd_row("Male", "24.8")
    female = _ihd_row("Female", "10.2")
    # Call order for a male request: user's row, then Male + Female cohort rows.
    session = _FakeSession([male, male, female])

    resp = asyncio.run(get_awareness(session, "male", 53))

    assert resp is not None
    assert resp.context.sex_label == "men"
    assert resp.context.age_band == "41 to 59"
    assert resp.context.cause_label == "ischaemic heart diseases"
    assert resp.context.share_percent == 24.8
    assert resp.context.rank_label == "number one"
    assert resp.context.one_in == 4
    assert [r.group_label for r in resp.reference_rows] == [
        "Malaysian men, 41-59",
        "Malaysian women, 41-59",
    ]
    assert resp.reference_rows[1].share_percent == 10.2
    assert resp.reference_rows[1].one_in == 10
    assert resp.source_label == "Department of Statistics Malaysia (DOSM)"


def test_get_awareness_returns_none_when_no_row():
    session = _FakeSession([None])
    assert asyncio.run(get_awareness(session, "male", 5)) is None
