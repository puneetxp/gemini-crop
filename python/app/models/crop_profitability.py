from __future__ import annotations
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from datetime import datetime as _datetime


class CropProfitability(BaseModel):
    id: int
    created_at: datetime
    updated_at: datetime
    enable: int
    crop_type: str
    variety: str | None = None
    state: str
    district: str | None = None
    year: int
    season: str | None = None
    avg_profit_per_acre: float
    min_profit_per_acre: float | None = None
    max_profit_per_acre: float | None = None
    seed_cost: float | None = None
    fertilizer_cost: float | None = None
    pesticide_cost: float | None = None
    labor_cost: float | None = None
    irrigation_cost: float | None = None
    equipment_cost: float | None = None
    other_costs: float | None = None
    total_investment_cost: float | None = None
    avg_revenue_per_acre: float | None = None
    roi_percentage: float | None = None
    break_even_yield: float | None = None
    profit_margin: float | None = None
    risk_level: str | None = None
    price_risk_score: float | None = None
    yield_risk_score: float | None = None
    market_demand: str | None = None
    competition_level: str | None = None
    data_source: str | None = None
    sample_size: int | None = None


class CropProfitabilityInput(BaseModel):
    enable: int | None = None
    crop_type: str | None = None
    variety: str | None = None
    state: str | None = None
    district: str | None = None
    year: int | None = None
    season: str | None = None
    avg_profit_per_acre: float | None = None
    min_profit_per_acre: float | None = None
    max_profit_per_acre: float | None = None
    seed_cost: float | None = None
    fertilizer_cost: float | None = None
    pesticide_cost: float | None = None
    labor_cost: float | None = None
    irrigation_cost: float | None = None
    equipment_cost: float | None = None
    other_costs: float | None = None
    total_investment_cost: float | None = None
    avg_revenue_per_acre: float | None = None
    roi_percentage: float | None = None
    break_even_yield: float | None = None
    profit_margin: float | None = None
    risk_level: str | None = None
    price_risk_score: float | None = None
    yield_risk_score: float | None = None
    market_demand: str | None = None
    competition_level: str | None = None
    data_source: str | None = None
    sample_size: int | None = None
