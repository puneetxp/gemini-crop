from __future__ import annotations
from pydantic import BaseModel
from typing import Optional, Any, Dict
from datetime import date, datetime
from datetime import date as _date, datetime as _datetime


class LivestockRoiPrediction(BaseModel):
    id: int
    created_at: datetime
    updated_at: datetime
    enable: int
    prediction_date: date
    prediction_type: str | None = None
    species: str
    breed: str
    age_months: int | None = None
    purpose: str
    purchase_price: float
    initial_setup_cost: float | None = None
    total_initial_investment: float
    monthly_feed_cost: float
    monthly_healthcare_cost: float | None = None
    monthly_labor_cost: float | None = None
    monthly_other_costs: float | None = None
    total_monthly_cost: float
    monthly_milk_revenue: float | None = None
    monthly_egg_revenue: float | None = None
    monthly_wool_revenue: float | None = None
    monthly_manure_revenue: float | None = None
    total_monthly_revenue: float | None = None
    offspring_revenue_per_year: float | None = None
    expected_sale_value: float | None = None
    expected_productive_years: int | None = None
    break_even_months: int
    break_even_date: date | None = None
    roi_1_year: float | None = None
    roi_2_year: float | None = None
    roi_5_year: float | None = None
    roi_percentage_1_year: float | None = None
    roi_percentage_2_year: float | None = None
    roi_percentage_5_year: float | None = None
    monthly_net_profit: float | None = None
    annual_net_profit: float | None = None
    lifetime_net_profit: float | None = None
    comparison_with_alternatives: Dict[str, Any] | None = None
    market_price_trends: Dict[str, Any] | None = None
    risk_level: str | None = None
    risk_factors: Dict[str, Any] | None = None
    mortality_risk: float | None = None
    disease_risk: float | None = None
    market_risk: float | None = None
    confidence_score: float | None = None
    key_assumptions: Dict[str, Any] | None = None
    sensitivity_analysis: Dict[str, Any] | None = None
    recommendation: str | None = None
    optimization_suggestions: Dict[str, Any] | None = None
    market_data_source: str | None = None
    breed_performance_data_source: str | None = None
    animal_id: int | None = None
    user_id: int | None = None


class LivestockRoiPredictionInput(BaseModel):
    enable: int | None = None
    prediction_date: _date | None = None
    prediction_type: str | None = None
    species: str | None = None
    breed: str | None = None
    age_months: int | None = None
    purpose: str | None = None
    purchase_price: float | None = None
    initial_setup_cost: float | None = None
    total_initial_investment: float | None = None
    monthly_feed_cost: float | None = None
    monthly_healthcare_cost: float | None = None
    monthly_labor_cost: float | None = None
    monthly_other_costs: float | None = None
    total_monthly_cost: float | None = None
    monthly_milk_revenue: float | None = None
    monthly_egg_revenue: float | None = None
    monthly_wool_revenue: float | None = None
    monthly_manure_revenue: float | None = None
    total_monthly_revenue: float | None = None
    offspring_revenue_per_year: float | None = None
    expected_sale_value: float | None = None
    expected_productive_years: int | None = None
    break_even_months: int | None = None
    break_even_date: _date | None = None
    roi_1_year: float | None = None
    roi_2_year: float | None = None
    roi_5_year: float | None = None
    roi_percentage_1_year: float | None = None
    roi_percentage_2_year: float | None = None
    roi_percentage_5_year: float | None = None
    monthly_net_profit: float | None = None
    annual_net_profit: float | None = None
    lifetime_net_profit: float | None = None
    comparison_with_alternatives: Dict[str, Any] | None = None
    market_price_trends: Dict[str, Any] | None = None
    risk_level: str | None = None
    risk_factors: Dict[str, Any] | None = None
    mortality_risk: float | None = None
    disease_risk: float | None = None
    market_risk: float | None = None
    confidence_score: float | None = None
    key_assumptions: Dict[str, Any] | None = None
    sensitivity_analysis: Dict[str, Any] | None = None
    recommendation: str | None = None
    optimization_suggestions: Dict[str, Any] | None = None
    market_data_source: str | None = None
    breed_performance_data_source: str | None = None
    animal_id: int | None = None
    user_id: int | None = None
