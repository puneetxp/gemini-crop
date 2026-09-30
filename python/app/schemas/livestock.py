"""
Livestock Pydantic schemas for request/response validation
"""

from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field, field_validator

from app.schemas.types import JsonDecimal


class LivestockBase(BaseModel):
    """Base livestock schema with common fields"""

    farm_id: int = Field(..., description="Farm ID where livestock is kept")
    farmer_id: int = Field(..., description="Farmer/owner ID")
    species: str = Field(..., description="Species: cattle, goat, poultry, buffalo")
    breed: str = Field(..., description="Breed name")
    quantity: int = Field(default=1, ge=1, description="Number of animals")
    purchase_price: JsonDecimal = Field(..., ge=0, description="Purchase price in INR")
    purchase_date: date = Field(..., description="Date of purchase")
    purpose: str = Field(..., description="Purpose: dairy, meat, breeding, eggs")
    status: str = Field(default="active", description="Status: active, sold, deceased")

    # Livestock location (can differ from farm address)
    latitude: Optional[JsonDecimal] = Field(None, description="GPS latitude (optional)")
    longitude: Optional[JsonDecimal] = Field(None, description="GPS longitude (optional)")
    pincode: Optional[str] = Field(None, max_length=10, description="Postal code")
    state: Optional[str] = Field(None, max_length=100, description="State")
    district: Optional[str] = Field(None, max_length=100, description="District")
    village: Optional[str] = Field(None, max_length=100, description="Village/VPO")
    address_line: Optional[str] = Field(None, max_length=255, description="Address line")

    @field_validator("species")
    @classmethod
    def validate_species(cls, v: str) -> str:
        """Validate species is one of allowed values"""
        allowed = ["cattle", "goat", "poultry", "buffalo"]
        if v.lower() not in allowed:
            raise ValueError(f"Species must be one of: {', '.join(allowed)}")
        return v.lower()

    @field_validator("purpose")
    @classmethod
    def validate_purpose(cls, v: str) -> str:
        """Validate purpose is one of allowed values"""
        allowed = ["dairy", "meat", "breeding", "eggs"]
        if v.lower() not in allowed:
            raise ValueError(f"Purpose must be one of: {', '.join(allowed)}")
        return v.lower()

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: str) -> str:
        """Validate status is one of allowed values"""
        allowed = ["active", "sold", "deceased"]
        if v.lower() not in allowed:
            raise ValueError(f"Status must be one of: {', '.join(allowed)}")
        return v.lower()


class LivestockCreate(LivestockBase):
    """Schema for creating new livestock"""

    pass


class LivestockUpdate(BaseModel):
    """Schema for updating livestock"""

    farm_id: Optional[int] = None
    species: Optional[str] = None
    breed: Optional[str] = None
    quantity: Optional[int] = Field(None, ge=1)
    purchase_price: Optional[JsonDecimal] = Field(None, ge=0)
    purchase_date: Optional[date] = None
    purpose: Optional[str] = None
    status: Optional[str] = None
    expected_roi: Optional[JsonDecimal] = None
    break_even_date: Optional[date] = None

    # Livestock location fields
    latitude: Optional[JsonDecimal] = None
    longitude: Optional[JsonDecimal] = None
    pincode: Optional[str] = Field(None, max_length=10)
    state: Optional[str] = Field(None, max_length=100)
    district: Optional[str] = Field(None, max_length=100)
    village: Optional[str] = Field(None, max_length=100)
    address_line: Optional[str] = Field(None, max_length=255)

    @field_validator("species")
    @classmethod
    def validate_species(cls, v: Optional[str]) -> Optional[str]:
        """Validate species if provided"""
        if v is None:
            return v
        allowed = ["cattle", "goat", "poultry", "buffalo"]
        if v.lower() not in allowed:
            raise ValueError(f"Species must be one of: {', '.join(allowed)}")
        return v.lower()

    @field_validator("purpose")
    @classmethod
    def validate_purpose(cls, v: Optional[str]) -> Optional[str]:
        """Validate purpose if provided"""
        if v is None:
            return v
        allowed = ["dairy", "meat", "breeding", "eggs"]
        if v.lower() not in allowed:
            raise ValueError(f"Purpose must be one of: {', '.join(allowed)}")
        return v.lower()

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: Optional[str]) -> Optional[str]:
        """Validate status if provided"""
        if v is None:
            return v
        allowed = ["active", "sold", "deceased"]
        if v.lower() not in allowed:
            raise ValueError(f"Status must be one of: {', '.join(allowed)}")
        return v.lower()


class LivestockResponse(LivestockBase):
    """Schema for livestock response"""

    id: int
    expected_roi: Optional[JsonDecimal] = None
    break_even_date: Optional[date] = None
    created_at: datetime
    updated_at: datetime
    enable: int = 1

    # Include location fields in response
    latitude: Optional[JsonDecimal] = None
    longitude: Optional[JsonDecimal] = None
    pincode: Optional[str] = None
    state: Optional[str] = None
    district: Optional[str] = None
    village: Optional[str] = None
    address_line: Optional[str] = None

    class Config:
        from_attributes = True


class LivestockWithROI(LivestockResponse):
    """Schema for livestock with calculated ROI metrics"""

    roi_metrics: Optional[dict] = Field(None, description="Calculated ROI metrics")


class LivestockPortfolioDashboard(BaseModel):
    """Schema for livestock portfolio dashboard"""

    total_livestock: int = Field(..., description="Total number of livestock")
    total_investment: JsonDecimal = Field(..., description="Total investment in INR")
    total_expected_returns: JsonDecimal = Field(..., description="Total expected returns in INR")
    total_current_value: JsonDecimal = Field(..., description="Current portfolio value in INR")
    overall_roi_percentage: JsonDecimal = Field(..., description="Overall ROI percentage")
    livestock_by_species: dict = Field(..., description="Breakdown by species")
    livestock_by_purpose: dict = Field(..., description="Breakdown by purpose")
    active_livestock: int = Field(..., description="Number of active livestock")
    break_even_summary: dict = Field(..., description="Break-even status summary")
