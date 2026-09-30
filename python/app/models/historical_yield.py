from __future__ import annotations
from pydantic import BaseModel
from typing import Optional, Any, Dict
from datetime import datetime
from datetime import datetime as _datetime


class HistoricalYield(BaseModel):
    id: int
    created_at: datetime
    updated_at: datetime
    enable: int
    crop_type: str
    variety: str | None = None
    state: str
    district: str | None = None
    block: str | None = None
    year: int
    season: str | None = None
    avg_yield_per_acre: float
    min_yield: float | None = None
    max_yield: float | None = None
    success_rate: float | None = None
    farmer_count: int | None = None
    total_area_cultivated: float | None = None
    soil_types: Dict[str, Any] | None = None
    irrigation_methods: Dict[str, Any] | None = None
    avg_rainfall: float | None = None
    avg_temperature: float | None = None
    quality_distribution: Dict[str, Any] | None = None
    avg_quality_grade: str | None = None
    data_source: str | None = None
    data_quality_score: float | None = None


class HistoricalYieldInput(BaseModel):
    enable: int | None = None
    crop_type: str | None = None
    variety: str | None = None
    state: str | None = None
    district: str | None = None
    block: str | None = None
    year: int | None = None
    season: str | None = None
    avg_yield_per_acre: float | None = None
    min_yield: float | None = None
    max_yield: float | None = None
    success_rate: float | None = None
    farmer_count: int | None = None
    total_area_cultivated: float | None = None
    soil_types: Dict[str, Any] | None = None
    irrigation_methods: Dict[str, Any] | None = None
    avg_rainfall: float | None = None
    avg_temperature: float | None = None
    quality_distribution: Dict[str, Any] | None = None
    avg_quality_grade: str | None = None
    data_source: str | None = None
    data_quality_score: float | None = None
