"""Routes for GET /api/clinics and GET /api/clinics/clusters."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_session
from app.modules.clinics.schema import ClinicsResponse, ClustersResponse
from app.modules.clinics.service import (
    build_clinics_response,
    build_clusters_response,
    fetch_all_clinics,
)

router = APIRouter(prefix="/api", tags=["clinics"])


@router.get("/clinics", response_model=ClinicsResponse)
async def read_clinics(
    q: str | None = None,
    state: str | None = None,
    type_: str | None = Query(None, alias="type"),
    limit: int = Query(20, ge=1, le=200),
    offset: int = Query(0, ge=0),
    session: AsyncSession = Depends(get_session),
) -> ClinicsResponse:
    clinics = await fetch_all_clinics(session)
    return build_clinics_response(clinics, q, state, type_, limit, offset)


@router.get("/clinics/clusters", response_model=ClustersResponse)
async def read_clinic_clusters(
    q: str | None = None,
    state: str | None = None,
    type_: str | None = Query(None, alias="type"),
    session: AsyncSession = Depends(get_session),
) -> ClustersResponse:
    clinics = await fetch_all_clinics(session)
    return build_clusters_response(clinics, q, state, type_)
