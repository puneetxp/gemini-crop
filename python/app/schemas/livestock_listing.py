"""
Livestock Listing Schemas

Pydantic models for livestock marketplace listing validation and serialization.
Supports comprehensive livestock information including health records, breeding
certifications, and media uploads.

Compatible with Python 3.14.3, Pydantic 2.10.5
"""

from datetime import date, datetime
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field, field_validator


class SpeciesEnum(str, Enum):
    """Livestock species"""

    CATTLE = "cattle"
    GOAT = "goat"
    SHEEP = "sheep"
    POULTRY = "poultry"
    BUFFALO = "buffalo"


class PurposeEnum(str, Enum):
    """Livestock purpose"""

    DAIRY = "dairy"
    MEAT = "meat"
    BREEDING = "breeding"
    DRAFT = "draft"
    EGGS = "eggs"


class GenderEnum(str, Enum):
    """Livestock gender"""

    MALE = "male"
    FEMALE = "female"
    MIXED = "mixed"


class HealthStatusEnum(str, Enum):
    """Health status"""

    HEALTHY = "healthy"
    RECOVERING = "recovering"
    PREGNANT = "pregnant"
    LACTATING = "lactating"


class VaccinationStatusEnum(str, Enum):
    """Vaccination status"""

    UP_TO_DATE = "up_to_date"
    PARTIAL = "partial"
    NONE = "none"


class ListingStatusEnum(str, Enum):
    """Listing status"""

    ACTIVE = "active"
    SOLD = "sold"
    RESERVED = "reserved"
    INACTIVE = "inactive"


class LivestockListingBase(BaseModel):
    """Base livestock listing schema"""

    livestock_id: int = Field(..., description="ID of the livestock being listed")
    title: str = Field(..., min_length=5, max_length=255, description="Listing title")
    description: Optional[str] = Field(None, description="Detailed description")
    species: SpeciesEnum = Field(..., description="Livestock species")
    breed: str = Field(..., min_length=2, max_length=255, description="Breed name")
    age_years: Optional[int] = Field(None, ge=0, le=30, description="Age in years")
    age_months: Optional[int] = Field(None, ge=0, le=11, description="Additional months")
    gender: GenderEnum = Field(..., description="Gender")
    quantity: int = Field(1, ge=1, le=1000, description="Number of animals")
    purpose: PurposeEnum = Field(..., description="Primary purpose")
    price: float = Field(..., gt=0, description="Price in INR")
    price_negotiable: bool = Field(True, description="Whether price is negotiable")
    weight_kg: Optional[float] = Field(None, gt=0, description="Weight in kilograms")
    health_status: HealthStatusEnum = Field(
        HealthStatusEnum.HEALTHY, description="Current health status"
    )
    vaccination_status: Optional[VaccinationStatusEnum] = Field(
        None, description="Vaccination status"
    )
    last_vaccination_date: Optional[date] = Field(None, description="Last vaccination date")
    milk_production_liters: Optional[float] = Field(None, ge=0, description="Daily milk production")
    breeding_certified: bool = Field(False, description="Has breeding certification")
    breeding_certification_number: Optional[str] = Field(
        None, max_length=255, description="Certification number"
    )
    genetic_lineage: Optional[str] = Field(None, description="Parent breed information")
    location_state: str = Field(..., min_length=2, max_length=100, description="State")
    location_district: str = Field(..., min_length=2, max_length=100, description="District")
    location_village: Optional[str] = Field(None, max_length=100, description="Village")
    latitude: Optional[float] = Field(None, ge=-90, le=90, description="GPS latitude")
    longitude: Optional[float] = Field(None, ge=-180, le=180, description="GPS longitude")
    pincode: Optional[str] = Field(None, pattern=r"^\d{6}$", description="6-digit pincode")
    address_line: Optional[str] = Field(None, max_length=255, description="Address line")
    farmer_contact_phone: Optional[str] = Field(None, max_length=20, description="Contact phone")
    farmer_contact_email: Optional[str] = Field(None, max_length=255, description="Contact email")


class LivestockListingCreate(LivestockListingBase):
    """Schema for creating a livestock listing"""

    farmer_id: int = Field(..., description="ID of the farmer creating the listing")
    photos: Optional[List[str]] = Field(None, description="List of photo URLs")
    videos: Optional[List[str]] = Field(None, description="List of video URLs")

    @field_validator("photos")
    @classmethod
    def validate_photos(cls, v):
        if v and len(v) > 10:
            raise ValueError("Maximum 10 photos allowed")
        return v

    @field_validator("videos")
    @classmethod
    def validate_videos(cls, v):
        if v and len(v) > 3:
            raise ValueError("Maximum 3 videos allowed")
        return v


class LivestockListingUpdate(BaseModel):
    """Schema for updating a livestock listing"""

    title: Optional[str] = Field(None, min_length=5, max_length=255)
    description: Optional[str] = None
    age_years: Optional[int] = Field(None, ge=0, le=30)
    age_months: Optional[int] = Field(None, ge=0, le=11)
    quantity: Optional[int] = Field(None, ge=1, le=1000)
    price: Optional[float] = Field(None, gt=0)
    price_negotiable: Optional[bool] = None
    weight_kg: Optional[float] = Field(None, gt=0)
    health_status: Optional[HealthStatusEnum] = None
    vaccination_status: Optional[VaccinationStatusEnum] = None
    last_vaccination_date: Optional[date] = None
    milk_production_liters: Optional[float] = Field(None, ge=0)
    breeding_certified: Optional[bool] = None
    breeding_certification_number: Optional[str] = Field(None, max_length=255)
    genetic_lineage: Optional[str] = None
    location_village: Optional[str] = Field(None, max_length=100)
    latitude: Optional[float] = Field(None, ge=-90, le=90)
    longitude: Optional[float] = Field(None, ge=-180, le=180)
    pincode: Optional[str] = Field(None, pattern=r"^\d{6}$")
    address_line: Optional[str] = Field(None, max_length=255)
    farmer_contact_phone: Optional[str] = Field(None, max_length=20)
    farmer_contact_email: Optional[str] = Field(None, max_length=255)
    status: Optional[ListingStatusEnum] = None
    featured: Optional[bool] = None
    photos: Optional[List[str]] = None
    videos: Optional[List[str]] = None


class LivestockListingResponse(LivestockListingBase):
    """Schema for livestock listing response"""

    id: int
    farmer_id: int
    photos: List[str] = Field(default_factory=list, description="List of photo URLs")
    videos: List[str] = Field(default_factory=list, description="List of video URLs")
    status: ListingStatusEnum
    views_count: int = 0
    interest_count: int = 0
    inquiry_count: int = 0
    featured: bool = False
    featured_until: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class LivestockListingSearchFilters(BaseModel):
    """Search filters for livestock listings"""

    species: Optional[SpeciesEnum] = None
    breed: Optional[str] = None
    purpose: Optional[PurposeEnum] = None
    min_price: Optional[float] = Field(None, ge=0)
    max_price: Optional[float] = Field(None, ge=0)
    min_age_months: Optional[int] = Field(None, ge=0)
    max_age_months: Optional[int] = Field(None, ge=0)
    gender: Optional[GenderEnum] = None
    location_state: Optional[str] = None
    location_district: Optional[str] = None
    health_status: Optional[HealthStatusEnum] = None
    vaccination_status: Optional[VaccinationStatusEnum] = None
    breeding_certified: Optional[bool] = None
    status: Optional[ListingStatusEnum] = Field(ListingStatusEnum.ACTIVE)
    featured_only: bool = False
    skip: int = Field(0, ge=0)
    limit: int = Field(20, ge=1, le=100)
    sort_by: str = Field("created_at", pattern="^(created_at|price|views_count|interest_count)$")
    sort_order: str = Field("desc", pattern="^(asc|desc)$")


class LivestockListingAnalytics(BaseModel):
    """Analytics for a livestock listing"""

    listing_id: int
    views_count: int
    interest_count: int
    inquiry_count: int
    views_last_7_days: int
    views_last_30_days: int
    interest_last_7_days: int
    interest_last_30_days: int
    average_daily_views: float
    conversion_rate: float = Field(..., description="Interest to views ratio")


class MediaUploadRequest(BaseModel):
    """Request for media upload URL"""

    filename: str = Field(..., description="Original filename")
    content_type: str = Field(..., description="MIME type")
    file_size: int = Field(..., gt=0, le=10485760, description="File size in bytes (max 10MB)")


class MediaUploadResponse(BaseModel):
    """Response with presigned upload URL"""

    upload_url: str = Field(..., description="Presigned S3 upload URL")
    file_url: str = Field(..., description="Final S3 file URL after upload")
    expires_in: int = Field(..., description="URL expiration time in seconds")
