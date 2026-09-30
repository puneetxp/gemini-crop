from __future__ import annotations
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from datetime import datetime as _datetime


class SlusiLccReport(BaseModel):
    id: int
    created_at: datetime
    updated_at: datetime
    enable: int
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
    spatial_available: bool | None = None
    non_spatial_available: bool | None = None
    ingested_at: datetime


class SlusiLccReportInput(BaseModel):
    enable: int | None = None
    state: str | None = None
    district: str | None = None
    report_no: str | None = None
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
    spatial_available: bool | None = None
    non_spatial_available: bool | None = None
    ingested_at: _datetime | None = None
