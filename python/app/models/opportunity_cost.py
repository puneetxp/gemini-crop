from __future__ import annotations
from pydantic import BaseModel
from typing import Optional, Any, Dict
from datetime import datetime
from datetime import datetime as _datetime


class OpportunityCost(BaseModel):
    id: int
    created_at: datetime
    updated_at: datetime
    enable: int
    location_state: str
    location_district: str | None = None
    primary_crop: str
    alternative_crop: str
    season: str | None = None
    year: int | None = None
    primary_crop_profit: float
    alternative_crop_profit: float
    profit_difference: float
    primary_crop_investment: float | None = None
    alternative_crop_investment: float | None = None
    investment_difference: float | None = None
    primary_crop_roi: float | None = None
    alternative_crop_roi: float | None = None
    roi_difference: float | None = None
    primary_crop_risk: str | None = None
    alternative_crop_risk: str | None = None
    risk_factor: float | None = None
    primary_crop_demand: str | None = None
    alternative_crop_demand: str | None = None
    market_stability_comparison: str | None = None
    recommended_choice: str | None = None
    recommendation_confidence: float | None = None
    recommendation_reasoning: str | None = None
    soil_suitability_comparison: Dict[str, Any] | None = None
    water_requirement_comparison: Dict[str, Any] | None = None
    labor_requirement_comparison: Dict[str, Any] | None = None


class OpportunityCostInput(BaseModel):
    enable: int | None = None
    location_state: str | None = None
    location_district: str | None = None
    primary_crop: str | None = None
    alternative_crop: str | None = None
    season: str | None = None
    year: int | None = None
    primary_crop_profit: float | None = None
    alternative_crop_profit: float | None = None
    profit_difference: float | None = None
    primary_crop_investment: float | None = None
    alternative_crop_investment: float | None = None
    investment_difference: float | None = None
    primary_crop_roi: float | None = None
    alternative_crop_roi: float | None = None
    roi_difference: float | None = None
    primary_crop_risk: str | None = None
    alternative_crop_risk: str | None = None
    risk_factor: float | None = None
    primary_crop_demand: str | None = None
    alternative_crop_demand: str | None = None
    market_stability_comparison: str | None = None
    recommended_choice: str | None = None
    recommendation_confidence: float | None = None
    recommendation_reasoning: str | None = None
    soil_suitability_comparison: Dict[str, Any] | None = None
    water_requirement_comparison: Dict[str, Any] | None = None
    labor_requirement_comparison: Dict[str, Any] | None = None
