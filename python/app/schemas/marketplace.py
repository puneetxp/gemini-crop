"""
Marketplace Pydantic schemas for request/response validation
"""

from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field, field_validator

from app.schemas.types import JsonDecimal


class MarketplaceListingBase(BaseModel):
    """Base marketplace listing schema"""

    farm_id: int = Field(..., description="Farm ID")
    farmer_id: int = Field(..., description="Farmer ID")
    crop_type: str = Field(..., description="Crop type")
    crop_variety: Optional[str] = Field(None, description="Crop variety")
    expected_harvest_date: date = Field(..., description="Expected harvest date")
    estimated_quantity: int = Field(..., ge=0, description="Estimated quantity in kg")
    available_quantity: Optional[int] = Field(None, ge=0, description="Available quantity in kg")
    quality_grade: Optional[str] = Field(None, description="Quality grade: A, B, C")
    location_state: str = Field(..., description="Farm state")
    location_district: str = Field(..., description="Farm district")
    farmer_contact_phone: Optional[str] = Field(None, description="Farmer phone")
    farmer_contact_email: Optional[str] = Field(None, description="Farmer email")
    status: str = Field(
        default="active", description="Status: active, booked, harvested, cancelled"
    )

    # Delivery address fields
    delivery_latitude: Optional[JsonDecimal] = Field(
        None, description="Delivery GPS latitude (optional)"
    )
    delivery_longitude: Optional[JsonDecimal] = Field(
        None, description="Delivery GPS longitude (optional)"
    )
    delivery_pincode: Optional[str] = Field(None, max_length=10, description="Delivery postal code")
    delivery_village: Optional[str] = Field(
        None, max_length=100, description="Delivery village/VPO"
    )
    delivery_address_line: Optional[str] = Field(
        None, max_length=255, description="Delivery address line"
    )

    @field_validator("quality_grade")
    @classmethod
    def validate_quality_grade(cls, v: Optional[str]) -> Optional[str]:
        """Validate quality grade"""
        if v is None:
            return v
        allowed = ["A", "B", "C"]
        if v.upper() not in allowed:
            raise ValueError(f"Quality grade must be one of: {', '.join(allowed)}")
        return v.upper()

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: str) -> str:
        """Validate status"""
        allowed = ["active", "booked", "harvested", "cancelled"]
        if v.lower() not in allowed:
            raise ValueError(f"Status must be one of: {', '.join(allowed)}")
        return v.lower()


class MarketplaceListingCreate(MarketplaceListingBase):
    """Schema for creating marketplace listing"""

    pass


class MarketplaceListingUpdate(BaseModel):
    """Schema for updating marketplace listing"""

    crop_type: Optional[str] = None
    crop_variety: Optional[str] = None
    expected_harvest_date: Optional[date] = None
    estimated_quantity: Optional[int] = Field(None, ge=0)
    available_quantity: Optional[int] = Field(None, ge=0)
    quality_grade: Optional[str] = None
    location_state: Optional[str] = None
    location_district: Optional[str] = None
    farmer_contact_phone: Optional[str] = None
    farmer_contact_email: Optional[str] = None
    status: Optional[str] = None

    # Delivery address fields
    delivery_latitude: Optional[JsonDecimal] = None
    delivery_longitude: Optional[JsonDecimal] = None
    delivery_pincode: Optional[str] = Field(None, max_length=10)
    delivery_village: Optional[str] = Field(None, max_length=100)
    delivery_address_line: Optional[str] = Field(None, max_length=255)

    @field_validator("quality_grade")
    @classmethod
    def validate_quality_grade(cls, v: Optional[str]) -> Optional[str]:
        """Validate quality grade if provided"""
        if v is None:
            return v
        allowed = ["A", "B", "C"]
        if v.upper() not in allowed:
            raise ValueError(f"Quality grade must be one of: {', '.join(allowed)}")
        return v.upper()

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: Optional[str]) -> Optional[str]:
        """Validate status if provided"""
        if v is None:
            return v
        allowed = ["active", "booked", "harvested", "cancelled"]
        if v.lower() not in allowed:
            raise ValueError(f"Status must be one of: {', '.join(allowed)}")
        return v.lower()


class MarketplaceListingResponse(MarketplaceListingBase):
    """Schema for marketplace listing response"""

    id: int
    created_at: datetime
    updated_at: datetime
    enable: int = 1

    class Config:
        from_attributes = True


class BuyerInterestBase(BaseModel):
    """Base buyer interest schema"""

    listing_id: int = Field(..., description="Marketplace listing ID")
    buyer_name: str = Field(..., description="Buyer name")
    buyer_phone: str = Field(..., description="Buyer phone")
    buyer_email: Optional[str] = Field(None, description="Buyer email")
    buyer_type: str = Field(
        ..., description="Buyer type: wholesaler, retailer, processor, cooperative"
    )
    interested_quantity: int = Field(..., ge=0, description="Interested quantity in kg")
    message: Optional[str] = Field(None, description="Message to farmer")
    status: str = Field(
        default="pending", description="Status: pending, contacted, agreed, cancelled"
    )

    # Buyer delivery address fields
    delivery_latitude: Optional[JsonDecimal] = Field(
        None, description="Buyer delivery GPS latitude (optional)"
    )
    delivery_longitude: Optional[JsonDecimal] = Field(
        None, description="Buyer delivery GPS longitude (optional)"
    )
    delivery_pincode: Optional[str] = Field(
        None, max_length=10, description="Buyer delivery postal code"
    )
    delivery_state: Optional[str] = Field(None, max_length=100, description="Buyer delivery state")
    delivery_district: Optional[str] = Field(
        None, max_length=100, description="Buyer delivery district"
    )
    delivery_village: Optional[str] = Field(
        None, max_length=100, description="Buyer delivery village/VPO"
    )
    delivery_address_line: Optional[str] = Field(
        None, max_length=255, description="Buyer delivery address line"
    )

    @field_validator("buyer_type")
    @classmethod
    def validate_buyer_type(cls, v: str) -> str:
        """Validate buyer type"""
        allowed = ["wholesaler", "retailer", "processor", "cooperative"]
        if v.lower() not in allowed:
            raise ValueError(f"Buyer type must be one of: {', '.join(allowed)}")
        return v.lower()

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: str) -> str:
        """Validate status"""
        allowed = ["pending", "contacted", "agreed", "cancelled"]
        if v.lower() not in allowed:
            raise ValueError(f"Status must be one of: {', '.join(allowed)}")
        return v.lower()


class BuyerInterestCreate(BuyerInterestBase):
    """Schema for creating buyer interest"""

    pass


class BuyerInterestUpdate(BaseModel):
    """Schema for updating buyer interest"""

    buyer_name: Optional[str] = None
    buyer_phone: Optional[str] = None
    buyer_email: Optional[str] = None
    buyer_type: Optional[str] = None
    interested_quantity: Optional[int] = Field(None, ge=0)
    message: Optional[str] = None
    status: Optional[str] = None

    # Buyer delivery address fields
    delivery_latitude: Optional[JsonDecimal] = None
    delivery_longitude: Optional[JsonDecimal] = None
    delivery_pincode: Optional[str] = Field(None, max_length=10)
    delivery_state: Optional[str] = Field(None, max_length=100)
    delivery_district: Optional[str] = Field(None, max_length=100)
    delivery_village: Optional[str] = Field(None, max_length=100)
    delivery_address_line: Optional[str] = Field(None, max_length=255)

    @field_validator("buyer_type")
    @classmethod
    def validate_buyer_type(cls, v: Optional[str]) -> Optional[str]:
        """Validate buyer type if provided"""
        if v is None:
            return v
        allowed = ["wholesaler", "retailer", "processor", "cooperative"]
        if v.lower() not in allowed:
            raise ValueError(f"Buyer type must be one of: {', '.join(allowed)}")
        return v.lower()

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: Optional[str]) -> Optional[str]:
        """Validate status if provided"""
        if v is None:
            return v
        allowed = ["pending", "contacted", "agreed", "cancelled"]
        if v.lower() not in allowed:
            raise ValueError(f"Status must be one of: {', '.join(allowed)}")
        return v.lower()


class BuyerInterestResponse(BuyerInterestBase):
    """Schema for buyer interest response"""

    id: int
    created_at: datetime
    updated_at: datetime
    enable: int = 1

    class Config:
        from_attributes = True
