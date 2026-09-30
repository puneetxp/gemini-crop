"""SLUSI Service — orchestrates DSS/Microwatershed ingestion and serves cached soil data."""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timedelta, timezone
from typing import Any  # db kept for compatibility; queries use app.core.db.DB
from typing import Any as Session

import httpx
from bs4 import BeautifulSoup
from fastapi import HTTPException

from app.schemas.slusi import (
    FarmSoilProfile,
    IngestionRunResult,
    LCCReport,
    LCCSummary,
    SLUSIStatus,
)
from app.services.dss_parser import DSSParser, SchemaMismatchError
from app.services.farm_access import run_named

logger = logging.getLogger(__name__)

DSS_URL = "https://slusi.da.gov.in/dss/dss_report_wise.html"
MWA_URL = "https://slusi.da.gov.in/mwanew.html"
_RETRY_COUNT = 3
_RETRY_DELAY = 10  # seconds
_MAP_FRESHNESS_DAYS = 30

# LCC classes that indicate land unsuitable / marginally suitable for cultivation
_POOR_LCC_CLASSES = {"V", "VI", "VII", "VIII"}


class SLUSIService:
    """Queries run as raw SQL through app.core.db.DB (run_named keeps the :name params); each statement autocommits."""

    def __init__(self, db: Session = None) -> None:
        self.db = db
        self._parser = DSSParser()

    # ------------------------------------------------------------------
    # 7.1  Ingest LCC data
    # ------------------------------------------------------------------

    async def ingest_lcc_data(self) -> int:
        """Fetch DSS HTML, parse, upsert into slusi_lcc_reports. Returns upsert count."""
        html = await self._fetch_with_retry(DSS_URL)
        reports = self._parser.parse(html)

        upserted = 0
        for report in reports:
            run_named(
                ("""
                    INSERT INTO slusi_lcc_reports
                        (state, district, report_no, year, total_area_ha,
                         lcc_class_i, lcc_class_ii, lcc_class_iii, lcc_class_iv,
                         lcc_class_v, lcc_class_vi, lcc_class_vii, lcc_class_viii,
                         forest_area, miscellaneous_area,
                         spatial_available, non_spatial_available, ingested_at)
                    VALUES
                        (:state, :district, :report_no, :year, :total_area_ha,
                         :lcc_class_i, :lcc_class_ii, :lcc_class_iii, :lcc_class_iv,
                         :lcc_class_v, :lcc_class_vi, :lcc_class_vii, :lcc_class_viii,
                         :forest_area, :miscellaneous_area,
                         :spatial_available, :non_spatial_available, :ingested_at)
                    ON CONFLICT (state, district, report_no) DO UPDATE SET
                        year                  = EXCLUDED.year,
                        total_area_ha         = EXCLUDED.total_area_ha,
                        lcc_class_i           = EXCLUDED.lcc_class_i,
                        lcc_class_ii          = EXCLUDED.lcc_class_ii,
                        lcc_class_iii         = EXCLUDED.lcc_class_iii,
                        lcc_class_iv          = EXCLUDED.lcc_class_iv,
                        lcc_class_v           = EXCLUDED.lcc_class_v,
                        lcc_class_vi          = EXCLUDED.lcc_class_vi,
                        lcc_class_vii         = EXCLUDED.lcc_class_vii,
                        lcc_class_viii        = EXCLUDED.lcc_class_viii,
                        forest_area           = EXCLUDED.forest_area,
                        miscellaneous_area    = EXCLUDED.miscellaneous_area,
                        spatial_available     = EXCLUDED.spatial_available,
                        non_spatial_available = EXCLUDED.non_spatial_available,
                        ingested_at           = EXCLUDED.ingested_at
                    """),
                {
                    "state": report.state,
                    "district": report.district,
                    "report_no": report.report_no,
                    "year": report.year,
                    "total_area_ha": report.total_area_ha,
                    "lcc_class_i": report.lcc_class_i,
                    "lcc_class_ii": report.lcc_class_ii,
                    "lcc_class_iii": report.lcc_class_iii,
                    "lcc_class_iv": report.lcc_class_iv,
                    "lcc_class_v": report.lcc_class_v,
                    "lcc_class_vi": report.lcc_class_vi,
                    "lcc_class_vii": report.lcc_class_vii,
                    "lcc_class_viii": report.lcc_class_viii,
                    "forest_area": report.forest_area,
                    "miscellaneous_area": report.miscellaneous_area,
                    "spatial_available": report.spatial_available,
                    "non_spatial_available": report.non_spatial_available,
                    "ingested_at": report.ingested_at,
                },
            )
            upserted += 1

        # committed by DB.raw
        logger.info("ingest_lcc_data: upserted %d records", upserted)
        return upserted

    # ------------------------------------------------------------------
    # 7.2  Ingest microwatershed maps
    # ------------------------------------------------------------------

    async def ingest_microwatershed_maps(self) -> int:
        """Download state PNG maps from SLUSI. Returns count of maps downloaded."""
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.get(MWA_URL)
            if resp.status_code != 200:
                logger.error("Failed to fetch microwatershed state list: HTTP %d", resp.status_code)
                return 0

            soup = BeautifulSoup(resp.text, "html.parser")
            state_links: list[tuple[str, str]] = []
            for a in soup.find_all("a", href=True):
                href: str = a["href"]
                if href.lower().endswith(".png"):
                    state_name = a.get_text(strip=True) or href
                    if not href.startswith("http"):
                        href = "https://slusi.da.gov.in/" + href.lstrip("/")
                    state_links.append((state_name, href))

            if not state_links:
                logger.warning("No PNG links found on microwatershed page")
                return 0

            cutoff = datetime.now(timezone.utc) - timedelta(days=_MAP_FRESHNESS_DAYS)
            downloaded = 0

            for state_name, png_url in state_links:
                # Check freshness
                row = run_named(
                    (
                        "SELECT ingested_at FROM slusi_microwatershed_maps "
                        "WHERE LOWER(state) = LOWER(:state)"
                    ),
                    {"state": state_name},
                ).fetchone()

                if row is not None:
                    ingested_at = row[0]
                    if ingested_at.tzinfo is None:
                        ingested_at = ingested_at.replace(tzinfo=timezone.utc)
                    if ingested_at >= cutoff:
                        logger.debug(
                            "Skipping %s — map fresh (ingested %s)", state_name, ingested_at
                        )
                        continue

                # Download PNG
                try:
                    png_resp = await client.get(png_url)
                    if png_resp.status_code != 200:
                        logger.warning(
                            "Failed to download map for %s: HTTP %d",
                            state_name,
                            png_resp.status_code,
                        )
                        continue
                    map_data = png_resp.content
                except Exception as exc:
                    logger.warning("Error downloading map for %s: %s", state_name, exc)
                    continue

                # Upsert
                run_named(
                    ("""
                        INSERT INTO slusi_microwatershed_maps
                            (state, map_data, file_size_bytes, ingested_at)
                        VALUES
                            (:state, :map_data, :file_size_bytes, :ingested_at)
                        ON CONFLICT (state) DO UPDATE SET
                            map_data        = EXCLUDED.map_data,
                            file_size_bytes = EXCLUDED.file_size_bytes,
                            ingested_at     = EXCLUDED.ingested_at
                        """),
                    {
                        "state": state_name,
                        "map_data": map_data,
                        "file_size_bytes": len(map_data),
                        "ingested_at": datetime.now(timezone.utc),
                    },
                )
                # committed by DB.raw
                downloaded += 1
                logger.info(
                    "Downloaded microwatershed map for %s (%d bytes)", state_name, len(map_data)
                )

        logger.info("ingest_microwatershed_maps: downloaded %d maps", downloaded)
        return downloaded

    # ------------------------------------------------------------------
    # 7.3  Run ingestion
    # ------------------------------------------------------------------

    @staticmethod
    def _ensure_upsert_index() -> None:
        """
        ingest_lcc_data upserts ON CONFLICT (state, district, report_no). The model JSON
        declares that as unique_constraints, but the schema generator does not emit it,
        so create the matching unique index here if it is missing.
        """
        run_named(
            "CREATE UNIQUE INDEX IF NOT EXISTS uq_lcc_state_district_report "
            "ON slusi_lcc_reports (state, district, report_no)"
        )

    async def run_ingestion(self) -> IngestionRunResult:
        """
        Orchestrate a full ingestion run.
        Raises HTTPException(409) if a run is already in progress.
        """
        # Check for running lock
        running = run_named(
            ("SELECT id FROM slusi_ingestion_runs WHERE status = 'running' LIMIT 1")
        ).fetchone()
        if running is not None:
            raise HTTPException(status_code=409, detail="An ingestion run is already in progress")

        self._ensure_upsert_index()

        started_at = datetime.now(timezone.utc)
        result = run_named(
            ("""
                INSERT INTO slusi_ingestion_runs (started_at, status, lcc_records_ingested, maps_ingested)
                VALUES (:started_at, 'running', 0, 0)
                RETURNING id
                """),
            {"started_at": started_at},
        )
        new_row = result.fetchone()
        run_id: int = new_row[0] if new_row is not None else 0
        # committed by DB.raw

        lcc_count = 0
        maps_count = 0
        error_message: str | None = None
        status = "success"

        try:
            lcc_count = await self.ingest_lcc_data()
            maps_count = await self.ingest_microwatershed_maps()
        except Exception as exc:
            logger.exception("Ingestion run %d failed: %s", run_id, exc)
            error_message = str(exc)
            status = "failed"

        completed_at = datetime.now(timezone.utc)
        run_named(
            ("""
                UPDATE slusi_ingestion_runs
                SET status                = :status,
                    lcc_records_ingested  = :lcc_records_ingested,
                    maps_ingested         = :maps_ingested,
                    completed_at          = :completed_at,
                    error_message         = :error_message
                WHERE id = :run_id
                """),
            {
                "status": status,
                "lcc_records_ingested": lcc_count,
                "maps_ingested": maps_count,
                "completed_at": completed_at,
                "error_message": error_message,
                "run_id": run_id,
            },
        )
        # committed by DB.raw

        return IngestionRunResult(
            run_id=run_id,
            status=status,
            lcc_records_ingested=lcc_count,
            maps_ingested=maps_count,
            started_at=started_at,
            completed_at=completed_at,
            error_message=error_message,
        )

    # ------------------------------------------------------------------
    # 7.4  Get LCC reports
    # ------------------------------------------------------------------

    def get_lcc_reports(
        self, state: str, district: str, year: int | None = None
    ) -> list[LCCReport]:
        """Return LCC reports for state/district, optionally filtered by year, sorted year DESC."""
        if year is not None:
            rows = run_named(
                ("""
                    SELECT state, district, report_no, year, total_area_ha,
                           lcc_class_i, lcc_class_ii, lcc_class_iii, lcc_class_iv,
                           lcc_class_v, lcc_class_vi, lcc_class_vii, lcc_class_viii,
                           forest_area, miscellaneous_area,
                           spatial_available, non_spatial_available, ingested_at
                    FROM slusi_lcc_reports
                    WHERE LOWER(state) = LOWER(:state)
                      AND LOWER(district) = LOWER(:district)
                      AND year = :year
                    ORDER BY year DESC NULLS LAST
                    """),
                {"state": state, "district": district, "year": year},
            ).fetchall()
        else:
            rows = run_named(
                ("""
                    SELECT state, district, report_no, year, total_area_ha,
                           lcc_class_i, lcc_class_ii, lcc_class_iii, lcc_class_iv,
                           lcc_class_v, lcc_class_vi, lcc_class_vii, lcc_class_viii,
                           forest_area, miscellaneous_area,
                           spatial_available, non_spatial_available, ingested_at
                    FROM slusi_lcc_reports
                    WHERE LOWER(state) = LOWER(:state)
                      AND LOWER(district) = LOWER(:district)
                    ORDER BY year DESC NULLS LAST
                    """),
                {"state": state, "district": district},
            ).fetchall()

        return [
            LCCReport(
                state=row[0],
                district=row[1],
                report_no=row[2],
                year=row[3],
                total_area_ha=row[4],
                lcc_class_i=row[5],
                lcc_class_ii=row[6],
                lcc_class_iii=row[7],
                lcc_class_iv=row[8],
                lcc_class_v=row[9],
                lcc_class_vi=row[10],
                lcc_class_vii=row[11],
                lcc_class_viii=row[12],
                forest_area=row[13],
                miscellaneous_area=row[14],
                spatial_available=bool(row[15]),
                non_spatial_available=bool(row[16]),
                ingested_at=row[17],
            )
            for row in rows
        ]

    # ------------------------------------------------------------------
    # 7.5  Get microwatershed map + status
    # ------------------------------------------------------------------

    def get_microwatershed_map(self, state: str) -> bytes | None:
        """Return PNG bytes for the given state, or None if not found."""
        row = run_named(
            (
                "SELECT map_data FROM slusi_microwatershed_maps "
                "WHERE LOWER(state) = LOWER(:state)"
            ),
            {"state": state},
        ).fetchone()
        return bytes(row[0]) if row is not None else None

    def get_status(self) -> SLUSIStatus:
        """Return last successful ingestion timestamp, total LCC records, states with maps."""
        last_run = run_named(
            (
                "SELECT completed_at FROM slusi_ingestion_runs "
                "WHERE status = 'success' "
                "ORDER BY completed_at DESC NULLS LAST LIMIT 1"
            )
        ).fetchone()

        total_lcc = run_named(("SELECT COUNT(*) FROM slusi_lcc_reports")).scalar() or 0

        states_with_maps = (
            run_named(("SELECT COUNT(*) FROM slusi_microwatershed_maps")).scalar() or 0
        )

        return SLUSIStatus(
            last_successful_ingestion=last_run[0] if last_run else None,
            total_lcc_records=int(total_lcc),
            states_with_maps=int(states_with_maps),
        )

    # ------------------------------------------------------------------
    # 7.6  Enrich farm profile
    # ------------------------------------------------------------------

    def enrich_farm_profile(self, farm: dict[str, Any]) -> FarmSoilProfile:
        """
        Attach the most recent LCC summary to a farm dict.
        Sets lcc_data_available=False when no records found.
        Sets lcc_limitation_warning when dominant class is V–VIII.
        """
        farm_id: int = int(farm.get("id") or 0)
        state: str = str(farm.get("location_state") or "")
        district: str = str(farm.get("location_district") or "")

        if not state or not district:
            return FarmSoilProfile(farm_id=farm_id, lcc_data_available=False)

        reports = self.get_lcc_reports(state, district)
        if not reports:
            return FarmSoilProfile(farm_id=farm_id, lcc_data_available=False)

        # Most recent report (already sorted DESC)
        report = reports[0]

        # Compute dominant LCC class
        class_areas: dict[str, float | None] = {
            "I": report.lcc_class_i,
            "II": report.lcc_class_ii,
            "III": report.lcc_class_iii,
            "IV": report.lcc_class_iv,
            "V": report.lcc_class_v,
            "VI": report.lcc_class_vi,
            "VII": report.lcc_class_vii,
            "VIII": report.lcc_class_viii,
        }
        valid_classes = {k: v for k, v in class_areas.items() if v is not None}
        dominant_class: str | None = (
            max(valid_classes, key=lambda k: valid_classes[k]) if valid_classes else None
        )

        lcc_summary = LCCSummary(
            dominant_class=dominant_class,
            total_area_ha=report.total_area_ha,
            data_source="SLUSI DSS",
            report_no=report.report_no,
            year=report.year,
            ingested_at=report.ingested_at,
        )

        limitation_warning: str | None = None
        if dominant_class in _POOR_LCC_CLASSES:
            limitation_warning = (
                f"Dominant LCC class {dominant_class} indicates land that is "
                "unsuitable or marginally suitable for cultivation. "
                "Consider soil conservation measures before farming."
            )

        return FarmSoilProfile(
            farm_id=farm_id,
            lcc_summary=lcc_summary,
            lcc_data_available=True,
            lcc_limitation_warning=limitation_warning,
        )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    async def _fetch_with_retry(self, url: str) -> str:
        """Fetch URL with up to _RETRY_COUNT retries on non-200 response."""
        last_exc: Exception | None = None
        async with httpx.AsyncClient(timeout=60) as client:
            for attempt in range(1, _RETRY_COUNT + 1):
                try:
                    resp = await client.get(url)
                    if resp.status_code == 200:
                        return resp.text
                    logger.warning(
                        "Attempt %d/%d: HTTP %d for %s",
                        attempt,
                        _RETRY_COUNT,
                        resp.status_code,
                        url,
                    )
                except Exception as exc:
                    logger.warning(
                        "Attempt %d/%d: request error for %s: %s", attempt, _RETRY_COUNT, url, exc
                    )
                    last_exc = exc

                if attempt < _RETRY_COUNT:
                    await asyncio.sleep(_RETRY_DELAY)

        raise RuntimeError(
            f"Failed to fetch {url} after {_RETRY_COUNT} attempts"
            + (f": {last_exc}" if last_exc else "")
        )
