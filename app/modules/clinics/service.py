"""Clinics service.

Text + state + type filtering, facet counts computed with the OTHER filter
applied (so choosing a state never empties the type list), limit/offset paging,
and per-state clusters with a centroid.

Filtering is done in Python over the fetched rows. The pure build_* functions
take a list of Clinic; fetch_all_clinics maps DB columns to the API field names.
"""

from __future__ import annotations

from collections.abc import Callable

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.clinics.model import PublicClinic
from app.modules.clinics.schema import (
    Clinic,
    ClinicFacets,
    ClinicsResponse,
    Cluster,
    ClustersResponse,
    Facet,
)

_TEXT_FIELDS = ("name", "district", "address", "state")


def _to_clinic(row: PublicClinic) -> Clinic:
    """Map a DB row to the API shape (facility_code -> id, etc.)."""
    return Clinic(
        id=row.facility_code,
        name=row.facility_name or "",
        type=row.facility_type or "",
        state=row.state or "",
        district=row.district or "",
        address=row.address or "N/A",
        phone=row.phone or "N/A",
        lat=float(row.latitude or 0),
        lng=float(row.longitude or 0),
    )


async def fetch_all_clinics(session: AsyncSession) -> list[Clinic]:
    rows = (await session.execute(select(PublicClinic))).scalars().all()
    return [_to_clinic(row) for row in rows]


def _matches_text(clinic: Clinic, q: str) -> bool:
    if not q:
        return True
    return any(q in getattr(clinic, field).lower() for field in _TEXT_FIELDS)


def _count_by(clinics: list[Clinic], key: Callable[[Clinic], str]) -> list[Facet]:
    counts: dict[str, int] = {}
    for clinic in clinics:
        value = key(clinic)
        counts[value] = counts.get(value, 0) + 1
    facets = [Facet(value=value, count=count) for value, count in counts.items()]
    facets.sort(key=lambda f: (-f.count, f.value))
    return facets


def _average(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def _normalize_filters(
    q: str | None, state: str | None, type_: str | None
) -> tuple[str, str, str]:
    """Trim and case-fold the filters (state/type match case-insensitively)."""
    return (q or "").strip().lower(), (state or "").strip().upper(), (type_ or "").strip().upper()


def _matches_state_type(clinic: Clinic, state: str, type_: str) -> bool:
    """Match against normalized state/type; an empty filter matches everything."""
    return (not state or clinic.state.upper() == state) and (
        not type_ or clinic.type.upper() == type_
    )


def build_clinics_response(
    all_clinics: list[Clinic],
    q: str | None = None,
    state: str | None = None,
    type_: str | None = None,
    limit: int = 20,
    offset: int = 0,
) -> ClinicsResponse:
    q, state, type_ = _normalize_filters(q, state, type_)

    by_text = [c for c in all_clinics if _matches_text(c, q)]
    matched = [c for c in by_text if _matches_state_type(c, state, type_)]

    return ClinicsResponse(
        total=len(all_clinics),
        filtered_total=len(matched),
        items=matched[offset : offset + limit],
        facets=ClinicFacets(
            # Counted with the OTHER filter applied, so picking a state never
            # empties the type list, and vice versa.
            states=_count_by(
                [c for c in by_text if _matches_state_type(c, "", type_)], lambda c: c.state
            ),
            types=_count_by(
                [c for c in by_text if _matches_state_type(c, state, "")], lambda c: c.type
            ),
        ),
    )


def build_clusters_response(
    all_clinics: list[Clinic],
    q: str | None = None,
    state: str | None = None,
    type_: str | None = None,
) -> ClustersResponse:
    q, state, type_ = _normalize_filters(q, state, type_)

    matched = [
        c for c in all_clinics if _matches_text(c, q) and _matches_state_type(c, state, type_)
    ]

    by_state: dict[str, list[Clinic]] = {}
    for clinic in matched:
        by_state.setdefault(clinic.state, []).append(clinic)

    clusters = [
        Cluster(
            state=state_name,
            count=len(clinics),
            lat=_average([c.lat for c in clinics]),
            lng=_average([c.lng for c in clinics]),
        )
        for state_name, clinics in by_state.items()
    ]
    return ClustersResponse(clusters=clusters)
