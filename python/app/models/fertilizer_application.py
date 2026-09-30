from __future__ import annotations
from pydantic import BaseModel
from typing import Optional
from datetime import date, datetime
from datetime import date as _date, datetime as _datetime


class FertilizerApplication(BaseModel):
    id: int
    created_at: datetime
    updated_at: datetime
    enable: int
    application_date: date
    fertilizer_type: str
    category: str
    quantity_kg: float
    quantity_per_hectare: float | None = None
    area_applied_hectares: float | None = None
    nitrogen_kg: float | None = None
    phosphorus_kg: float | None = None
    potassium_kg: float | None = None
    cost_total: float | None = None
    cost_per_kg: float | None = None
    cost_per_hectare: float | None = None
    application_method: str | None = None
    growth_stage: str | None = None
    days_after_planting: int | None = None
    effectiveness_score: float | None = None
    soil_response_notes: str | None = None
    weather_conditions: str | None = None
    temperature_celsius: float | None = None
    rainfall_mm_24h: float | None = None
    recommended_by: str | None = None
    recommendation_id: str | None = None
    notes: str | None = None
    farm_id: int
    plot_id: int | None = None
    crop_id: int | None = None
    soil_test_before_id: int | None = None
    soil_test_after_id: int | None = None


class FertilizerApplicationInput(BaseModel):
    enable: int | None = None
    application_date: _date | None = None
    fertilizer_type: str | None = None
    category: str | None = None
    quantity_kg: float | None = None
    quantity_per_hectare: float | None = None
    area_applied_hectares: float | None = None
    nitrogen_kg: float | None = None
    phosphorus_kg: float | None = None
    potassium_kg: float | None = None
    cost_total: float | None = None
    cost_per_kg: float | None = None
    cost_per_hectare: float | None = None
    application_method: str | None = None
    growth_stage: str | None = None
    days_after_planting: int | None = None
    effectiveness_score: float | None = None
    soil_response_notes: str | None = None
    weather_conditions: str | None = None
    temperature_celsius: float | None = None
    rainfall_mm_24h: float | None = None
    recommended_by: str | None = None
    recommendation_id: str | None = None
    notes: str | None = None
    farm_id: int | None = None
    plot_id: int | None = None
    crop_id: int | None = None
    soil_test_before_id: int | None = None
    soil_test_after_id: int | None = None
