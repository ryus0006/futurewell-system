"""Unit tests for the clinics service build functions.

Pure list-in / response-out, so no DB is needed. Fixtures span two states and
two types to exercise the cross-filter facet behavior.
"""

from app.modules.clinics.schema import Clinic
from app.modules.clinics.service import (
    build_clinics_response,
    build_clusters_response,
)


def _clinic(id_, name, type_, state, district, lat, lng) -> Clinic:
    return Clinic(
        id=id_,
        name=name,
        type=type_,
        state=state,
        district=district,
        address=f"Jalan {name}",
        phone="000",
        lat=lat,
        lng=lng,
    )


# A, B in Kuala Lumpur; C, D in Selangor. Types: KESIHATAN x3, KOMUNITI x1.
CLINICS = [
    _clinic("a", "Alpha", "KESIHATAN", "Kuala Lumpur", "Cheras", 3.0, 101.0),
    _clinic("b", "Beta", "KOMUNITI", "Kuala Lumpur", "Sentul", 3.2, 101.2),
    _clinic("c", "Charlie", "KESIHATAN", "Selangor", "Klang", 3.0, 101.4),
    _clinic("d", "Delta", "KESIHATAN", "Selangor", "Kajang", 3.1, 101.6),
]


def test_no_filters_returns_all():
    resp = build_clinics_response(CLINICS)
    assert resp.total == 4
    assert resp.filtered_total == 4
    assert len(resp.items) == 4


def test_state_filter_and_cross_facets():
    resp = build_clinics_response(CLINICS, state="Kuala Lumpur")
    assert resp.filtered_total == 2
    assert {c.id for c in resp.items} == {"a", "b"}
    # states facet is NOT emptied by the state filter (other filter = type, none)
    assert [(f.value, f.count) for f in resp.facets.states] == [
        ("Kuala Lumpur", 2),
        ("Selangor", 2),
    ]
    # types facet reflects only KL clinics (the selected state)
    assert [(f.value, f.count) for f in resp.facets.types] == [
        ("KESIHATAN", 1),
        ("KOMUNITI", 1),
    ]


def test_type_filter_facets_sorted_by_count_then_value():
    resp = build_clinics_response(CLINICS, type_="KESIHATAN")
    assert resp.filtered_total == 3
    # states facet counted among KESIHATAN clinics: Selangor 2, KL 1 (count desc)
    assert [(f.value, f.count) for f in resp.facets.states] == [
        ("Selangor", 2),
        ("Kuala Lumpur", 1),
    ]
    # types facet unaffected by type filter (other filter = state, none)
    assert [(f.value, f.count) for f in resp.facets.types] == [
        ("KESIHATAN", 3),
        ("KOMUNITI", 1),
    ]


def test_text_search_matches_name_and_district():
    assert build_clinics_response(CLINICS, q="charlie").filtered_total == 1  # name
    assert build_clinics_response(CLINICS, q="kajang").filtered_total == 1  # district
    assert build_clinics_response(CLINICS, q="kuala").filtered_total == 2  # state text


def test_pagination_slices_items_but_keeps_filtered_total():
    resp = build_clinics_response(CLINICS, limit=1, offset=1)
    assert resp.filtered_total == 4
    assert len(resp.items) == 1
    assert resp.items[0].id == "b"


def test_state_and_type_filters_are_case_insensitive():
    # Filtering is case-insensitive on state and type.
    for value in ("selangor", "Selangor", "SELANGOR"):
        assert build_clinics_response(CLINICS, state=value).filtered_total == 2
    for value in ("kesihatan", "KESIHATAN"):
        assert build_clinics_response(CLINICS, type_=value).filtered_total == 3


def test_clusters_group_by_state_with_centroid():
    resp = build_clusters_response(CLINICS, type_="KESIHATAN")
    by_state = {c.state: c for c in resp.clusters}
    assert by_state["Kuala Lumpur"].count == 1
    assert by_state["Selangor"].count == 2
    # Selangor centroid = mean of C and D
    assert by_state["Selangor"].lat == 3.05
    assert by_state["Selangor"].lng == 101.5
