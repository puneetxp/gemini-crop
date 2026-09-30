"""SLUSI soil data integration endpoints."""

from __future__ import annotations

import logging
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import DB, CurrentAdmin, CurrentUser
from app.schemas.slusi import (
    IngestionRunResult,
    LCCReport,
    SLUSIStatus,
    SoilLookupResponse,
)
from app.services.shc_code_mapper import SHCCodeMapper
from app.services.shc_fetcher import SHCFetcher
from app.services.slusi_service import SLUSIService

logger = logging.getLogger(__name__)

router = APIRouter(tags=["SLUSI Soil Data"])

# ---------------------------------------------------------------------------
# Dependency helpers
# ---------------------------------------------------------------------------


def get_slusi_service(db: DB) -> SLUSIService:
    return SLUSIService(db)


SLUSISvc = Annotated[SLUSIService, Depends(get_slusi_service)]


# ---------------------------------------------------------------------------
# GET /farms/soil-lookup  (JWT required)
# ---------------------------------------------------------------------------


@router.get("/farms/soil-lookup", response_model=SoilLookupResponse)
async def soil_lookup(
    current_user: CurrentUser,
    db: DB,
    lat: float = Query(..., ge=-90, le=90, description="Farm latitude"),
    lon: float = Query(..., ge=-180, le=180, description="Farm longitude"),
    state: Optional[str] = Query(None, description="State name (optional; same as /v2 when given)"),
    district: Optional[str] = Query(None, description="District name"),
) -> SoilLookupResponse:
    """
    Real-time SHC WMS lookup + LCC cache query for a GPS coordinate.
    Returns SHCSoilProfile and district LCC summary within 12 seconds.
    """
    service = SLUSIService(db)
    mapper = SHCCodeMapper()
    fetcher = SHCFetcher()

    # Resolve state/district from the user's registered location as a fallback;
    # the frontend should pass state/district as query params in a real call,
    # but for now we attempt to resolve from the coordinate via the DB.
    # For MVP: require state + district query params.
    if state and district:
        return await soil_lookup_v2(current_user, db, lat, lon, state, district)
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Please provide state and district query parameters for soil lookup",
    )


@router.get("/farms/soil-lookup/v2", response_model=SoilLookupResponse)
async def soil_lookup_v2(
    current_user: CurrentUser,
    db: DB,
    lat: float = Query(..., ge=-90, le=90),
    lon: float = Query(..., ge=-180, le=180),
    state: str = Query(..., description="State name"),
    district: str = Query(..., description="District name"),
) -> SoilLookupResponse:
    """
    Real-time SHC WMS lookup + LCC cache query.
    Accepts lat, lon, state, district. Returns combined soil profile within 12s.
    """
    service = SLUSIService(db)
    mapper = SHCCodeMapper()
    fetcher = SHCFetcher()

    codes = await mapper.resolve(state, district, db)
    if codes is None:
        logger.warning("soil_lookup: no WMS codes for state=%s district=%s", state, district)
        from app.schemas.slusi import LCCSummary, SHCSoilProfile

        shc_profile = SHCSoilProfile(wms_available=False, partial_data=True)
        lcc_reports = service.get_lcc_reports(state, district)
        lcc_summary = None
        lcc_available = False
        if lcc_reports:
            report = lcc_reports[0]
            class_areas = {
                "I": report.lcc_class_i,
                "II": report.lcc_class_ii,
                "III": report.lcc_class_iii,
                "IV": report.lcc_class_iv,
                "V": report.lcc_class_v,
                "VI": report.lcc_class_vi,
                "VII": report.lcc_class_vii,
                "VIII": report.lcc_class_viii,
            }
            valid = {k: v for k, v in class_areas.items() if v is not None}
            dominant = max(valid, key=lambda k: valid[k]) if valid else None
            lcc_summary = LCCSummary(
                dominant_class=dominant,
                total_area_ha=report.total_area_ha,
                report_no=report.report_no,
                year=report.year,
                ingested_at=report.ingested_at,
            )
            lcc_available = True
        return SoilLookupResponse(
            shc_profile=shc_profile,
            lcc_summary=lcc_summary,
            lcc_data_available=lcc_available,
        )

    state_code, district_code = codes
    shc_profile = await fetcher.fetch_soil_profile(lat, lon, state_code, district_code)

    farm_profile = service.enrich_farm_profile(
        {
            "id": 0,
            "location_state": state,
            "location_district": district,
        }
    )

    return SoilLookupResponse(
        shc_profile=shc_profile,
        lcc_summary=farm_profile.lcc_summary,
        lcc_data_available=farm_profile.lcc_data_available,
        lcc_limitation_warning=farm_profile.lcc_limitation_warning,
    )


# ---------------------------------------------------------------------------
# GET /slusi/lcc  (public, rate-limited)
# ---------------------------------------------------------------------------


@router.get("/slusi/lcc", response_model=list[LCCReport])
def get_lcc_reports(
    db: DB,
    state: str = Query(..., description="State name"),
    district: str = Query(..., description="District name"),
    year: int | None = Query(None, description="Filter by year"),
) -> list[LCCReport]:
    """Query LCC reports by state/district. Returns empty list when no data."""
    service = SLUSIService(db)
    return service.get_lcc_reports(state, district, year)


# ---------------------------------------------------------------------------
# GET /slusi/maps/{state}  (public)
# ---------------------------------------------------------------------------


@router.get("/slusi/maps/{state}")
def get_microwatershed_map(state: str, db: DB) -> Response:
    """Return microwatershed PNG for the given state. 404 if not available."""
    service = SLUSIService(db)
    data = service.get_microwatershed_map(state)
    if data is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Microwatershed map for '{state}' is not yet available. "
            "Run ingestion to download maps from SLUSI.",
        )
    return Response(content=data, media_type="image/png")


# ---------------------------------------------------------------------------
# POST /slusi/ingest  (admin JWT)
# ---------------------------------------------------------------------------


@router.post("/slusi/ingest", response_model=IngestionRunResult)
async def trigger_ingestion(
    current_admin: CurrentAdmin,
    db: DB,
) -> IngestionRunResult:
    """Trigger an immediate SLUSI ingestion run. Returns 409 if already running."""
    service = SLUSIService(db)
    return await service.run_ingestion()


# ---------------------------------------------------------------------------
# GET /slusi/status  (public)
# ---------------------------------------------------------------------------


@router.get("/slusi/status", response_model=SLUSIStatus)
def get_status(db: DB) -> SLUSIStatus:
    """Return last ingestion timestamp, LCC record count, and map count."""
    service = SLUSIService(db)
    return service.get_status()


# ---------------------------------------------------------------------------
# GET /slusi/config  (admin JWT)
# ---------------------------------------------------------------------------


@router.get("/slusi/config")
def get_config(current_admin: CurrentAdmin) -> dict[str, str]:
    """Return masked WMS config for diagnostics."""
    from app.core.config import settings

    wms_path = settings.SHC_WMS_PATH
    masked = ("*" * (len(wms_path) - 4) + wms_path[-4:]) if len(wms_path) >= 4 else "****"
    return {
        "shc_wms_path_masked": masked,
        "shc_cycle": settings.SHC_CYCLE,
        "slusi_ingest_interval_days": str(settings.SLUSI_INGEST_INTERVAL_DAYS),
    }
