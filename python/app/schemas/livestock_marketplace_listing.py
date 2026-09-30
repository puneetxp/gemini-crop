"""
Livestock Marketplace Listing Schemas
Pydantic models for request/response validation
"""

from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.types import JsonDecimal


class LivestockMarketplaceListingBase(BaseModel):
    """Base schema for livestock marketplace listing"""

    livestock_id: int = Field(..., description="ID of the livestock being listed")
    listing_type: str = Field(
        ..., description="Type of listing (sale, breeding_service, milk_production)"
    )
    asking_price: JsonDecimal = Field(..., gt=0, description="Asking price for the livestock")
    current_age_months: int = Field(..., gt=0, description="Current age in months")
    current_weight_kg: Optional[JsonDecimal] = Field(None, ge=0, description="Current weight in kg")
    milk_production_liters_per_day: Optional[JsonDecimal] = Field(
        None, ge=0, description="Daily milk production (for dairy)"
    )
    breeding_history: Optional[str] = Field(None, description="Breeding history details")
    health_status: str = Field(
        default="excellent", description="Health status (excellent, good, fair, poor)"
    )
    vaccination_status: str = Field(
        default="up_to_date", description="Vaccination status (up_to_date, pending, none)"
    )
    total_investment: JsonDecimal = Field(
        ..., gt=0, description="Total investment including purchase, feed, healthcare"
    )
    total_revenue: JsonDecimal = Field(
        default=0, ge=0, description="Total revenue generated so far"
    )
    location_state: str = Field(..., description="State where livestock is located")
    location_district: str = Field(..., description="District where livestock is located")
    farmer_contact_phone: str = Field(..., description="Farmer's contact phone number")
    farmer_contact_email: Optional[str] = Field(None, description="Farmer's contact email")


class LivestockMarketplaceListingCreate(LivestockMarketplaceListingBase):
    """Schema for creating a new livestock marketplace listing"""

    pass


class LivestockMarketplaceListingUpdate(BaseModel):
    """Schema for updating a livestock marketplace listing"""

    listing_type: Optional[str] = None
    asking_price: Optional[JsonDecimal] = None
    current_age_months: Optional[int] = None
    current_weight_kg: Optional[JsonDecimal] = None
    milk_production_liters_per_day: Optional[JsonDecimal] = None
    breeding_history: Optional[str] = None
    health_status: Optional[str] = None
    vaccination_status: Optional[str] = None
    total_investment: Optional[JsonDecimal] = None
    total_revenue: Optional[JsonDecimal] = None
    location_state: Optional[str] = None
    location_district: Optional[str] = None
    farmer_contact_phone: Optional[str] = None
    farmer_contact_email: Optional[str] = None
    listing_status: Optional[str] = None
    bedrock_analysis: Optional[str] = None


class LivestockMarketplaceListingResponse(LivestockMarketplaceListingBase):
    """Schema for livestock marketplace listing response"""

    id: int
    farmer_id: int
    current_roi_percentage: Optional[JsonDecimal] = None
    break_even_achieved: bool = False
    break_even_date: Optional[date] = None
    projected_annual_profit: Optional[JsonDecimal] = None
    listing_status: str = "active"
    views_count: int = 0
    bedrock_analysis: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class LivestockMarketplaceListingList(BaseModel):
    """Schema for paginated livestock marketplace listing list"""

    listings: List[LivestockMarketplaceListingResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
