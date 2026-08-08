"""Response DTOs for GET /api/clinics and /api/clinics/clusters.

The service maps DB columns to these API names (facility_code -> id,
facility_name -> name, facility_type -> type, latitude/longitude -> lat/lng).
"""

from pydantic import BaseModel


class Clinic(BaseModel):
    id: str
    name: str
    type: str
    state: str
    district: str
    address: str
    phone: str
    lat: float
    lng: float


class Facet(BaseModel):
    value: str
    count: int


class ClinicFacets(BaseModel):
    states: list[Facet]
    types: list[Facet]


class ClinicsResponse(BaseModel):
    total: int
    filtered_total: int
    items: list[Clinic]
    facets: ClinicFacets


class Cluster(BaseModel):
    lat: float
    lng: float
    count: int
    state: str


class ClustersResponse(BaseModel):
    clusters: list[Cluster]
