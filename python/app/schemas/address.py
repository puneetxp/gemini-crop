"""
Address Management Schemas

Pydantic models for address handling with optional GPS coordinates
and required pincode-based location.
"""

import re
from typing import Optional

from pydantic import BaseModel, Field, field_validator


class AddressBase(BaseModel):
    """Base address model with optional GPS and required pincode"""

    latitude: Optional[float] = Field(None, ge=-90, le=90, description="GPS latitude (optional)")
    longitude: Optional[float] = Field(
        None, ge=-180, le=180, description="GPS longitude (optional)"
    )
    pincode: str = Field(..., min_length=6, max_length=10, description="Postal code (required)")
    state: str = Field(..., min_length=2, max_length=100, description="State name (required)")
    district: str = Field(..., min_length=2, max_length=100, description="District name (required)")
    village: str = Field(
        ..., min_length=2, max_length=100, description="Village/VPO name (required)"
    )
    address_line: Optional[str] = Field(None, max_length=255, description="Full address (optional)")

    @field_validator("pincode")
    @classmethod
    def validate_pincode(cls, v: str) -> str:
        """Validate pincode format (6 digits for India)"""
        if not re.match(r"^\d{6}$", v):
            raise ValueError("Pincode must be 6 digits")
        return v

    @field_validator("latitude")
    @classmethod
    def validate_latitude_with_longitude(cls, v: Optional[float], info) -> Optional[float]:
        """If latitude provided, longitude should also be provided"""
        if v is not None:
            # Note: longitude validation happens in the model validator
            pass
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "latitude": 28.6139,
                "longitude": 77.2090,
                "pincode": "110001",
                "state": "Delhi",
                "district": "Central Delhi",
                "village": "Connaught Place",
                "address_line": "Block A, Sector 1, Near Metro Station",
            }
        }


class PincodeLookupResponse(BaseModel):
    """Response from pincode lookup API"""

    vpo: str = Field(..., description="Village Post Office name")
    pincode: str = Field(..., description="Postal code")
    district: str = Field(..., description="District name")
    state: str = Field(..., description="State name")

    class Config:
        json_schema_extra = {
            "example": {
                "vpo": "Connaught Place",
                "pincode": "110001",
                "district": "Central Delhi",
                "state": "Delhi",
            }
        }


class AddressAutoFillRequest(BaseModel):
    """Request for address auto-fill from pincode"""

    pincode: str = Field(..., min_length=6, max_length=6, description="6-digit Indian pincode")

    @field_validator("pincode")
    @classmethod
    def validate_pincode(cls, v: str) -> str:
        """Validate pincode format"""
        if not re.match(r"^\d{6}$", v):
            raise ValueError("Pincode must be 6 digits")
        return v


class AddressAutoFillResponse(BaseModel):
    """Response with auto-filled address data"""

    pincode: str
    state: str
    district: str
    villages: list[str] = Field(..., description="List of villages/VPOs for this pincode")

    class Config:
        json_schema_extra = {
            "example": {
                "pincode": "110001",
                "state": "Delhi",
                "district": "Central Delhi",
                "villages": ["Connaught Place", "Janpath", "Parliament Street"],
            }
        }


class UserAddressUpdate(BaseModel):
    """Update user personal address"""

    latitude: Optional[float] = Field(None, ge=-90, le=90)
    longitude: Optional[float] = Field(None, ge=-180, le=180)
    pincode: Optional[str] = Field(None, min_length=6, max_length=10)
    state: Optional[str] = Field(None, min_length=2, max_length=100)
    district: Optional[str] = Field(None, min_length=2, max_length=100)
    village: Optional[str] = Field(None, min_length=2, max_length=100)
    address_line: Optional[str] = Field(None, max_length=255)


class FarmAddressUpdate(BaseModel):
    """Update farm address"""

    latitude: Optional[float] = Field(None, ge=-90, le=90)
    longitude: Optional[float] = Field(None, ge=-180, le=180)
    pincode: Optional[str] = Field(None, min_length=6, max_length=10)
    state: Optional[str] = Field(None, min_length=2, max_length=100)
    district: Optional[str] = Field(None, min_length=2, max_length=100)
    village: Optional[str] = Field(None, min_length=2, max_length=100)
    address_line: Optional[str] = Field(None, max_length=255)


class LivestockAddressUpdate(BaseModel):
    """Update livestock location address"""

    latitude: Optional[float] = Field(None, ge=-90, le=90)
    longitude: Optional[float] = Field(None, ge=-180, le=180)
    pincode: Optional[str] = Field(None, min_length=6, max_length=10)
    state: Optional[str] = Field(None, min_length=2, max_length=100)
    district: Optional[str] = Field(None, min_length=2, max_length=100)
    village: Optional[str] = Field(None, min_length=2, max_length=100)
    address_line: Optional[str] = Field(None, max_length=255)


class DeliveryAddressUpdate(BaseModel):
    """Update delivery address for marketplace"""

    delivery_latitude: Optional[float] = Field(None, ge=-90, le=90)
    delivery_longitude: Optional[float] = Field(None, ge=-180, le=180)
    delivery_pincode: Optional[str] = Field(None, min_length=6, max_length=10)
    delivery_state: Optional[str] = Field(None, min_length=2, max_length=100)
    delivery_district: Optional[str] = Field(None, min_length=2, max_length=100)
    delivery_village: Optional[str] = Field(None, min_length=2, max_length=100)
    delivery_address_line: Optional[str] = Field(None, max_length=255)
