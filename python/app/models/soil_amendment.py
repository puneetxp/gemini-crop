from __future__ import annotations
from pydantic import BaseModel
from typing import Optional, Any, Dict
from datetime import date, datetime
from datetime import date as _date, datetime as _datetime


class SoilAmendment(BaseModel):
    id: int
    created_at: datetime
    updated_at: datetime
    enable: int
    amendment_date: date
    amendment_type: str
    amendment_name: str | None = None
    primary_purpose: str | None = None
    target_improvement: Dict[str, Any] | None = None
    quantity: float
    unit: str
    quantity_per_acre: float | None = None
    application_method: str | None = None
    incorporation_depth: float | None = None
    cost: float | None = None
    cost_per_acre: float | None = None
    organic_matter_content: float | None = None
    nutrient_content: Dict[str, Any] | None = None
    carbon_nitrogen_ratio: float | None = None
    current_ph: float | None = None
    target_ph: float | None = None
    expected_ph_change: float | None = None
    days_before_planting: int | None = None
    soil_moisture_at_application: str | None = None
    weather_conditions: Dict[str, Any] | None = None
    expected_benefits: Dict[str, Any] | None = None
    expected_duration_months: int | None = None
    actual_benefits: Dict[str, Any] | None = None
    effectiveness_rating: int | None = None
    recommendation_source: str | None = None
    recommended_by: str | None = None
    notes: str | None = None
    plot_id: int
    follow_up_soil_test_id: int | None = None


class SoilAmendmentInput(BaseModel):
    enable: int | None = None
    amendment_date: _date | None = None
    amendment_type: str | None = None
    amendment_name: str | None = None
    primary_purpose: str | None = None
    target_improvement: Dict[str, Any] | None = None
    quantity: float | None = None
    unit: str | None = None
    quantity_per_acre: float | None = None
    application_method: str | None = None
    incorporation_depth: float | None = None
    cost: float | None = None
    cost_per_acre: float | None = None
    organic_matter_content: float | None = None
    nutrient_content: Dict[str, Any] | None = None
    carbon_nitrogen_ratio: float | None = None
    current_ph: float | None = None
    target_ph: float | None = None
    expected_ph_change: float | None = None
    days_before_planting: int | None = None
    soil_moisture_at_application: str | None = None
    weather_conditions: Dict[str, Any] | None = None
    expected_benefits: Dict[str, Any] | None = None
    expected_duration_months: int | None = None
    actual_benefits: Dict[str, Any] | None = None
    effectiveness_rating: int | None = None
    recommendation_source: str | None = None
    recommended_by: str | None = None
    notes: str | None = None
    plot_id: int | None = None
    follow_up_soil_test_id: int | None = None
