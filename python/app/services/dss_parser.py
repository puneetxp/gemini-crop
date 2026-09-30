"""DSS HTML parser and PrettyPrinter for SLUSI LCC data."""

from __future__ import annotations

import json
import logging
import re
from datetime import datetime, timezone

from bs4 import BeautifulSoup

from app.schemas.slusi import LCCReport, SHCSoilProfile

logger = logging.getLogger(__name__)

# Expected DSS table column headers (case-insensitive substring match)
_EXPECTED_COLS = [
    "state",
    "district",
    "report",
    "year",
    "area",
    "class i",
    "class ii",
    "class iii",
    "class iv",
    "class v",
    "class vi",
    "class vii",
    "class viii",
    "forest",
    "misc",
]

# Column index mapping after header detection
_COL_MAP = {
    "state": 0,
    "district": 1,
    "report_no": 2,
    "year": 3,
    "total_area_ha": 4,
    "lcc_class_i": 5,
    "lcc_class_ii": 6,
    "lcc_class_iii": 7,
    "lcc_class_iv": 8,
    "lcc_class_v": 9,
    "lcc_class_vi": 10,
    "lcc_class_vii": 11,
    "lcc_class_viii": 12,
    "forest_area": 13,
    "miscellaneous_area": 14,
    "spatial_available": 15,
    "non_spatial_available": 16,
}

# Delimiter used by PrettyPrinter / parse_single_row
_SEP = "\t"


_ROMAN = ["i", "ii", "iii", "iv", "v", "vi", "vii", "viii"]


def _norm(value: str) -> str:
    """Collapse internal whitespace (the DSS page wraps names like 'Uttar \\n\\t Pradesh')."""
    return re.sub(r"\s+", " ", value).strip()


def _locate_columns(headers: list[str]) -> dict[str, int]:
    """Map LCCReport field names to column indexes using the header text."""
    col: dict[str, int] = {}
    for idx, h in enumerate(headers):
        if "non spatial" in h or "non-spatial" in h:
            col.setdefault("non_spatial_available", idx)
        elif "spatial" in h:
            col.setdefault("spatial_available", idx)
        elif "report" in h:
            col.setdefault("report_no", idx)
        elif "year" in h:
            col.setdefault("year", idx)
        elif "district" in h:
            col.setdefault("district", idx)
        elif "state" in h:
            col.setdefault("state", idx)
        elif "area" in h and "misc" not in h:
            col.setdefault("total_area_ha", idx)
        elif "forest" in h:
            col.setdefault("forest_area", idx)
        elif "misc" in h:
            col.setdefault("miscellaneous_area", idx)

    # LCC classes: either labelled individually ("Class I" ... "Class VIII") or as a run
    # of eight columns starting at "LCC:I" followed by bare "II", "III", ...
    for idx, h in enumerate(headers):
        m = re.fullmatch(r"(?:lcc\s*:?\s*|class\s+)?(i{1,3}|iv|vi{0,3})", h)
        if m and m.group(1) in _ROMAN:
            col.setdefault(f"lcc_class_{m.group(1)}", idx)
    return col


class SchemaMismatchError(Exception):
    """Raised when the DSS HTML table structure doesn't match expectations."""


def _parse_cell(value: str) -> float | None:
    """Return float for numeric strings, None for dash/empty."""
    v = value.strip()
    if v in ("", "-", "N/A", "NA"):
        return None
    try:
        return float(v.replace(",", ""))
    except ValueError:
        return None


def _parse_bool(value: str) -> bool:
    v = value.strip().lower()
    return v in ("yes", "true", "1", "y")


class DSSParser:
    """Parses the SLUSI DSS HTML table into LCCReport objects."""

    def parse(self, html: str) -> list[LCCReport]:
        """
        Parse DSS HTML table. Skips malformed rows with a warning.
        Raises SchemaMismatchError if expected columns are not found.

        The page has several layout tables (nav, banner) before the data table, and
        column order has changed over time, so the table is chosen by its header row
        and columns are located by header name rather than fixed position.
        """
        soup = BeautifulSoup(html, "html.parser")
        tables = soup.find_all("table")
        if not tables:
            raise SchemaMismatchError("No <table> found in DSS HTML")

        best: tuple[int, list[str], list] | None = None
        for table in tables:
            rows = table.find_all("tr")
            if not rows:
                continue
            headers = [_norm(c.get_text(" ")).lower() for c in rows[0].find_all(["th", "td"])]
            found = sum(1 for col in _EXPECTED_COLS if any(col in h for h in headers))
            if best is None or found > best[0]:
                best = (found, headers, rows)

        if best is None:
            raise SchemaMismatchError("DSS table has no rows")
        found, headers, rows = best
        if found < 5:
            raise SchemaMismatchError(
                f"DSS table schema mismatch: only {found}/{len(_EXPECTED_COLS)} "
                f"expected columns found. Headers: {headers}"
            )

        col = _locate_columns(headers)
        missing = [k for k in ("state", "district", "report_no") if k not in col]
        if missing:
            raise SchemaMismatchError(f"DSS table missing required columns {missing}: {headers}")

        reports: list[LCCReport] = []
        for row_idx, row in enumerate(rows[1:], start=1):
            cells = [_norm(td.get_text(" ")) for td in row.find_all(["td", "th"])]
            if len(cells) < len(headers) - 2:
                logger.warning("DSS row %d: too few cells (%d), skipping", row_idx, len(cells))
                continue

            def cell(key: str) -> str:
                idx = col.get(key)
                return cells[idx] if idx is not None and idx < len(cells) else ""

            try:
                year = cell("year")
                report = LCCReport(
                    state=cell("state"),
                    district=cell("district"),
                    report_no=cell("report_no"),
                    year=int(year) if year.isdigit() else None,
                    total_area_ha=_parse_cell(cell("total_area_ha")),
                    lcc_class_i=_parse_cell(cell("lcc_class_i")),
                    lcc_class_ii=_parse_cell(cell("lcc_class_ii")),
                    lcc_class_iii=_parse_cell(cell("lcc_class_iii")),
                    lcc_class_iv=_parse_cell(cell("lcc_class_iv")),
                    lcc_class_v=_parse_cell(cell("lcc_class_v")),
                    lcc_class_vi=_parse_cell(cell("lcc_class_vi")),
                    lcc_class_vii=_parse_cell(cell("lcc_class_vii")),
                    lcc_class_viii=_parse_cell(cell("lcc_class_viii")),
                    forest_area=_parse_cell(cell("forest_area")),
                    miscellaneous_area=_parse_cell(cell("miscellaneous_area")),
                    spatial_available=_parse_bool(cell("spatial_available")),
                    non_spatial_available=_parse_bool(cell("non_spatial_available")),
                    ingested_at=datetime.now(timezone.utc),
                )
                if not report.state or not report.district or not report.report_no:
                    logger.warning("DSS row %d: missing state/district/report, skipping", row_idx)
                    continue
                reports.append(report)
            except Exception as exc:
                logger.warning("DSS row %d: parse error (%s), skipping", row_idx, exc)

        return reports

    def parse_single_row(self, text: str) -> LCCReport:
        """
        Parse a single tab-separated row produced by PrettyPrinter.format_lcc_report.
        Used for round-trip property testing.
        """
        parts = text.split(_SEP)
        if len(parts) < 17:
            raise ValueError(f"Expected ≥17 tab-separated fields, got {len(parts)}")

        def _f(idx: int) -> float | None:
            return _parse_cell(parts[idx])

        def _b(idx: int) -> bool:
            return _parse_bool(parts[idx]) if idx < len(parts) else False

        return LCCReport(
            state=parts[0].strip(),
            district=parts[1].strip(),
            report_no=parts[2].strip(),
            year=int(parts[3]) if parts[3].strip().isdigit() else None,
            total_area_ha=_f(4),
            lcc_class_i=_f(5),
            lcc_class_ii=_f(6),
            lcc_class_iii=_f(7),
            lcc_class_iv=_f(8),
            lcc_class_v=_f(9),
            lcc_class_vi=_f(10),
            lcc_class_vii=_f(11),
            lcc_class_viii=_f(12),
            forest_area=_f(13),
            miscellaneous_area=_f(14),
            spatial_available=_b(15),
            non_spatial_available=_b(16),
            ingested_at=(
                datetime.fromisoformat(parts[17].strip())
                if len(parts) > 17
                else datetime.now(timezone.utc)
            ),
        )


class PrettyPrinter:
    """Formats SLUSI data structures back to human-readable / round-trippable text."""

    def format_lcc_report(self, report: LCCReport) -> str:
        """
        Serialise an LCCReport to a tab-separated string.
        Parseable back to an equivalent LCCReport via DSSParser.parse_single_row.
        """

        def _v(val: float | None) -> str:
            return str(val) if val is not None else "-"

        def _b(val: bool) -> str:
            return "yes" if val else "no"

        fields = [
            report.state,
            report.district,
            report.report_no,
            str(report.year) if report.year is not None else "-",
            _v(report.total_area_ha),
            _v(report.lcc_class_i),
            _v(report.lcc_class_ii),
            _v(report.lcc_class_iii),
            _v(report.lcc_class_iv),
            _v(report.lcc_class_v),
            _v(report.lcc_class_vi),
            _v(report.lcc_class_vii),
            _v(report.lcc_class_viii),
            _v(report.forest_area),
            _v(report.miscellaneous_area),
            _b(report.spatial_available),
            _b(report.non_spatial_available),
            report.ingested_at.isoformat(),
        ]
        return _SEP.join(fields)

    def format_shc_soil_profile(self, profile: SHCSoilProfile) -> dict[str, object]:
        """
        Serialise a SHCSoilProfile to a dict that can be deserialised back
        via SHCSoilProfile.model_validate (round-trip property).
        """
        return json.loads(profile.model_dump_json())
