"""Pydantic schemas for SLUSI soil data integration."""

from __future__ import annotations

from datetime import datetime, timezone

from pydantic import BaseModel, Field


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


# ---------------------------------------------------------------------------
# SHC WMS schemas
# ---------------------------------------------------------------------------


class SHCSoilProfile(BaseModel):
    """Soil profile collected from SHC WMS GetFeatureInfo calls."""

    # Nutrient values (decimal, kg/ha or ppm)
    nitrogen: float | None = None
    phosphorus: float | None = None
    potassium: float | None = None
    sulfur: float | None = None
    boron: float | None = None
    iron: float | None = None
    zinc: float | None = None
    copper: float | None = None
    manganese: float | None = None
    organic_carbon: float | None = None
    ph_level: float | None = None
    electrical_conductivity: float | None = None
    # Physical class values (string labels)
    soil_depth_class: str | None = None
    slope_class: str | None = None
    erosion_class: str | None = None
    soil_texture_class: str | None = None
    land_capability_class: str | None = None
    land_irrigability_class: str | None = None
    hydrological_soil_group: str | None = None
    # Metadata
    partial_data: bool = False
    wms_available: bool = True
    unavailable_styles: list[str] = Field(default_factory=list)
    fetched_at: datetime | None = None
    village_sample_count: int | None = None


# ---------------------------------------------------------------------------
# SLUSI LCC schemas
# ---------------------------------------------------------------------------


class LCCReport(BaseModel):
    """One row from the SLUSI DSS LCC table."""

    state: str
    district: str
    report_no: str
    year: int | None = None
    total_area_ha: float | None = None
    lcc_class_i: float | None = None
    lcc_class_ii: float | None = None
    lcc_class_iii: float | None = None
    lcc_class_iv: float | None = None
    lcc_class_v: float | None = None
    lcc_class_vi: float | None = None
    lcc_class_vii: float | None = None
    lcc_class_viii: float | None = None
    forest_area: float | None = None
    miscellaneous_area: float | None = None
    spatial_available: bool = False
    non_spatial_available: bool = False
    ingested_at: datetime = Field(default_factory=_utcnow)


class LCCSummary(BaseModel):
    """Aggregated LCC summary for a district (used in farm enrichment)."""

    dominant_class: str | None = None
    total_area_ha: float | None = None
    data_source: str = "SLUSI DSS"
    report_no: str | None = None
    year: int | None = None
    ingested_at: datetime | None = None


# ---------------------------------------------------------------------------
# Combined lookup response
# ---------------------------------------------------------------------------


class SoilLookupResponse(BaseModel):
    """Response from GET /farms/soil-lookup."""

    shc_profile: SHCSoilProfile
    lcc_summary: LCCSummary | None = None
    lcc_data_available: bool = False
    lcc_limitation_warning: str | None = None


# ---------------------------------------------------------------------------
# Farm enrichment
# ---------------------------------------------------------------------------


class FarmSoilProfile(BaseModel):
    """Enriched soil profile attached to a farm response."""

    farm_id: int
    shc_profile: SHCSoilProfile | None = None
    lcc_summary: LCCSummary | None = None
    lcc_data_available: bool = False
    lcc_limitation_warning: str | None = None


# ---------------------------------------------------------------------------
# Ingestion status / admin schemas
# ---------------------------------------------------------------------------


class SLUSIStatus(BaseModel):
    """Response from GET /slusi/status."""

    last_successful_ingestion: datetime | None = None
    total_lcc_records: int = 0
    states_with_maps: int = 0


class IngestionRunResult(BaseModel):
    """Result returned after an ingestion run completes."""

    run_id: int
    status: str  # 'success' | 'failed'
    lcc_records_ingested: int = 0
    maps_ingested: int = 0
    started_at: datetime
    completed_at: datetime | None = None
    error_message: str | None = None
