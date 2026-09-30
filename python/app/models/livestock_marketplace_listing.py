from __future__ import annotations
from pydantic import BaseModel
from typing import Optional
from datetime import date, datetime
from datetime import date as _date, datetime as _datetime


class LivestockMarketplaceListing(BaseModel):
    id: int
    created_at: datetime
    updated_at: datetime
    enable: int
    listing_type: str
    asking_price: float
    current_age_months: int
    current_weight_kg: float | None = None
    milk_production_liters_per_day: float | None = None
    breeding_history: str | None = None
    health_status: str | None = None
    vaccination_status: str | None = None
    total_investment: float
    total_revenue: float | None = None
    current_roi_percentage: float | None = None
    break_even_achieved: bool | None = None
    break_even_date: date | None = None
    projected_annual_profit: float | None = None
    location_state: str
    location_district: str
    farmer_contact_phone: str
    farmer_contact_email: str | None = None
    listing_status: str | None = None
    views_count: int | None = None
    bedrock_analysis: str | None = None
    livestock_id: int
    farmer_id: int


class LivestockMarketplaceListingInput(BaseModel):
    enable: int | None = None
    listing_type: str | None = None
    asking_price: float | None = None
    current_age_months: int | None = None
    current_weight_kg: float | None = None
    milk_production_liters_per_day: float | None = None
    breeding_history: str | None = None
    health_status: str | None = None
    vaccination_status: str | None = None
    total_investment: float | None = None
    total_revenue: float | None = None
    current_roi_percentage: float | None = None
    break_even_achieved: bool | None = None
    break_even_date: _date | None = None
    projected_annual_profit: float | None = None
    location_state: str | None = None
    location_district: str | None = None
    farmer_contact_phone: str | None = None
    farmer_contact_email: str | None = None
    listing_status: str | None = None
    views_count: int | None = None
    bedrock_analysis: str | None = None
    livestock_id: int | None = None
    farmer_id: int | None = None
