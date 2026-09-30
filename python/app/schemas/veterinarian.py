"""
Veterinarian directory Pydantic schemas for request/response validation
"""

from datetime import datetime
from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel, Field, model_validator


class VeterinarianBase(BaseModel):
    """Base veterinarian schema with common fields"""

    name: str = Field(..., min_length=1, max_length=255, description="Veterinarian's full name")
    clinic_name: Optional[str] = Field(None, description="Clinic or hospital name")
    specialization: Optional[str] = Field(
        None, description="e.g. large_animal, poultry, small_ruminant, general"
    )
    species_supported: Optional[List[str]] = Field(
        None, description="Species treated: cattle, buffalo, goat, poultry, sheep"
    )
    phone: str = Field(..., min_length=8, max_length=20, description="Phone number, tap-to-call")
    whatsapp: Optional[str] = Field(
        None, max_length=20, description="WhatsApp number if different from phone"
    )
    email: Optional[str] = Field(None, description="Email address")
    location_state: Optional[str] = Field(None, description="State served")
    location_district: Optional[str] = Field(None, description="District served")
    address: Optional[str] = Field(None, description="Clinic address")
    available_now: bool = Field(True, description="Currently available for consultation")
    notes: Optional[str] = Field(None, description="Experience, timings, or other notes")


class VeterinarianCreate(VeterinarianBase):
    """Schema for adding a veterinarian to the directory"""

    added_by_user_id: Optional[int] = Field(
        None, description="User who added this entry, if logged in"
    )

    @model_validator(mode="after")
    def require_a_contact_method(self) -> "VeterinarianCreate":
        if not self.phone and not self.whatsapp and not self.email:
            raise ValueError("At least one contact method (phone, whatsapp, or email) is required")
        return self


class VeterinarianUpdate(BaseModel):
    """Schema for updating a veterinarian entry"""

    name: Optional[str] = Field(None, min_length=1, max_length=255)
    clinic_name: Optional[str] = None
    specialization: Optional[str] = None
    species_supported: Optional[List[str]] = None
    phone: Optional[str] = Field(None, min_length=8, max_length=20)
    whatsapp: Optional[str] = None
    email: Optional[str] = None
    location_state: Optional[str] = None
    location_district: Optional[str] = None
    address: Optional[str] = None
    available_now: Optional[bool] = None
    verified: Optional[bool] = None
    notes: Optional[str] = None


class VeterinarianResponse(VeterinarianBase):
    """Schema for veterinarian response, including ready-to-use connect links"""

    id: int
    created_at: datetime
    updated_at: datetime
    verified: bool = False
    rating: float = 0.0  # float so JSON carries a number (Decimal serialises as a string)
    total_ratings: int = 0
    call_link: Optional[str] = Field(None, description="tel: link")
    whatsapp_link: Optional[str] = Field(None, description="wa.me link")
    email_link: Optional[str] = Field(None, description="mailto: link")

    class Config:
        from_attributes = True
