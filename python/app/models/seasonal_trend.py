from __future__ import annotations
from pydantic import BaseModel
from typing import Optional, Any, Dict
from datetime import date, datetime
from datetime import date as _date, datetime as _datetime


class SeasonalTrend(BaseModel):
    id: int
    created_at: datetime
    updated_at: datetime
    enable: int
    crop_type: str
    state: str
    district: str | None = None
    planting_season: str
    harvest_season: str | None = None
    optimal_planting_start: date | None = None
    optimal_planting_end: date | None = None
    optimal_harvest_start: date | None = None
    optimal_harvest_end: date | None = None
    avg_growth_duration_days: int | None = None
    price_trend_yoy: float | None = None
    demand_trend_yoy: float | None = None
    yield_trend_yoy: float | None = None
    weather_suitability_score: float | None = None
    pest_disease_risk: str | None = None
    market_timing_score: float | None = None
    avg_success_rate: float | None = None
    farmer_adoption_rate: float | None = None
    recommended_varieties: Dict[str, Any] | None = None
    companion_crops: Dict[str, Any] | None = None
    rotation_recommendations: Dict[str, Any] | None = None
    analysis_start_year: int | None = None
    analysis_end_year: int | None = None
    years_of_data: int | None = None


class SeasonalTrendInput(BaseModel):
    enable: int | None = None
    crop_type: str | None = None
    state: str | None = None
    district: str | None = None
    planting_season: str | None = None
    harvest_season: str | None = None
    optimal_planting_start: _date | None = None
    optimal_planting_end: _date | None = None
    optimal_harvest_start: _date | None = None
    optimal_harvest_end: _date | None = None
    avg_growth_duration_days: int | None = None
    price_trend_yoy: float | None = None
    demand_trend_yoy: float | None = None
    yield_trend_yoy: float | None = None
    weather_suitability_score: float | None = None
    pest_disease_risk: str | None = None
    market_timing_score: float | None = None
    avg_success_rate: float | None = None
    farmer_adoption_rate: float | None = None
    recommended_varieties: Dict[str, Any] | None = None
    companion_crops: Dict[str, Any] | None = None
    rotation_recommendations: Dict[str, Any] | None = None
    analysis_start_year: int | None = None
    analysis_end_year: int | None = None
    years_of_data: int | None = None
