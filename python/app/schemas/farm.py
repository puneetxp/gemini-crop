"""
Farm and Plot management schemas with enhanced validation and sanitization
"""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.core.validation import (
    EnumValidator,
    NumericRangeValidator,
    sanitize_input,
    validate_coordinates,
    validate_enum,
)


class PlotBase(BaseModel):
    """Base plot schema"""

    name: str = Field(..., min_length=1, max_length=100, description="Plot name")
    area_acres: float = Field(..., gt=0, description="Plot area in acres")
    soil_type: Optional[str] = Field(
        None, description="Soil type: clay, sandy, loamy, silt, peat, black, red, mixed"
    )
    irrigation_type: Optional[str] = Field(
        None, description="Irrigation: rain-fed, canal, borewell, drip, sprinkler, mixed"
    )
    nitrogen: Optional[float] = Field(None, ge=0, description="Nitrogen content (kg/ha)")
    phosphorus: Optional[float] = Field(None, ge=0, description="Phosphorus content (kg/ha)")
    potassium: Optional[float] = Field(None, ge=0, description="Potassium content (kg/ha)")
    ph_level: Optional[float] = Field(None, ge=0, le=14, description="pH level (0-14)")
    organic_carbon: Optional[float] = Field(None, ge=0, le=100, description="Organic carbon (%)")
    electrical_conductivity: Optional[float] = Field(None, ge=0, description="EC (dS/m)")
    sulfur: Optional[float] = Field(None, ge=0, description="Sulfur (ppm)")
    zinc: Optional[float] = Field(None, ge=0, description="Zinc (ppm)")
    iron: Optional[float] = Field(None, ge=0, description="Iron (ppm)")
    boron: Optional[float] = Field(None, ge=0, description="Boron (ppm)")

    @field_validator("name")
    @classmethod
    def sanitize_name(cls, v: str) -> str:
        """Sanitize plot name"""
        return sanitize_input(v, allow_html=False)

    @field_validator("area_acres")
    @classmethod
    def validate_area_range(cls, v: float) -> float:
        """Validate area is within acceptable range"""
        return NumericRangeValidator.validate_area(v, min_area=0.01, max_area=10000.0)

    @field_validator("soil_type")
    @classmethod
    def validate_soil_type_enum(cls, v: Optional[str]) -> Optional[str]:
        """Validate soil type"""
        if v is None:
            return v
        return validate_enum(v, EnumValidator.SOIL_TYPES, "soil_type")

    @field_validator("irrigation_type")
    @classmethod
    def validate_irrigation_type_enum(cls, v: Optional[str]) -> Optional[str]:
        """Validate irrigation type"""
        if v is None:
            return v
        return validate_enum(v, EnumValidator.IRRIGATION_TYPES, "irrigation_type")


class PlotCreate(PlotBase):
    """Plot creation schema"""

    pass


class PlotUpdate(BaseModel):
    """Plot update schema"""

    name: Optional[str] = Field(None, min_length=1, max_length=100)
    area_acres: Optional[float] = Field(None, gt=0)
    soil_type: Optional[str] = None
    irrigation_type: Optional[str] = None
    nitrogen: Optional[float] = Field(None, ge=0)
    phosphorus: Optional[float] = Field(None, ge=0)
    potassium: Optional[float] = Field(None, ge=0)
    ph_level: Optional[float] = Field(None, ge=0, le=14)
    organic_carbon: Optional[float] = Field(None, ge=0, le=100)
    electrical_conductivity: Optional[float] = Field(None, ge=0)
    sulfur: Optional[float] = Field(None, ge=0)
    zinc: Optional[float] = Field(None, ge=0)
    iron: Optional[float] = Field(None, ge=0)
    boron: Optional[float] = Field(None, ge=0)

    @field_validator("name")
    @classmethod
    def sanitize_name(cls, v: Optional[str]) -> Optional[str]:
        """Sanitize plot name"""
        if v is None:
            return v
        return sanitize_input(v, allow_html=False)

    @field_validator("area_acres")
    @classmethod
    def validate_area_range(cls, v: Optional[float]) -> Optional[float]:
        """Validate area"""
        if v is None:
            return v
        return NumericRangeValidator.validate_area(v, min_area=0.01, max_area=10000.0)

    @field_validator("soil_type")
    @classmethod
    def validate_soil_type_enum(cls, v: Optional[str]) -> Optional[str]:
        """Validate soil type"""
        if v is None:
            return v
        return validate_enum(v, EnumValidator.SOIL_TYPES, "soil_type")

    @field_validator("irrigation_type")
    @classmethod
    def validate_irrigation_type_enum(cls, v: Optional[str]) -> Optional[str]:
        """Validate irrigation type"""
        if v is None:
            return v
        return validate_enum(v, EnumValidator.IRRIGATION_TYPES, "irrigation_type")


class PlotResponse(PlotBase):
    """Plot response schema"""

    id: int = Field(..., description="Plot ID")
    farm_id: int = Field(..., description="Farm ID")
    is_active: bool = Field(..., description="Plot active status")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    nitrogen: Optional[float] = Field(None, description="Nitrogen content (kg/ha)")
    phosphorus: Optional[float] = Field(None, description="Phosphorus content (kg/ha)")
    potassium: Optional[float] = Field(None, description="Potassium content (kg/ha)")
    ph_level: Optional[float] = Field(None, description="pH level (0-14)")
    organic_carbon: Optional[float] = Field(None, description="Organic carbon (%)")
    electrical_conductivity: Optional[float] = Field(None, description="EC (dS/m)")
    sulfur: Optional[float] = Field(None, description="Sulfur (ppm)")
    zinc: Optional[float] = Field(None, description="Zinc (ppm)")
    iron: Optional[float] = Field(None, description="Iron (ppm)")
    boron: Optional[float] = Field(None, description="Boron (ppm)")

    model_config = ConfigDict(from_attributes=True)


class FarmBase(BaseModel):
    """Base farm schema with address support"""

    name: str = Field(..., min_length=1, max_length=200, description="Farm name")
    state: str = Field(..., min_length=2, max_length=100, description="State")
    district: str = Field(..., min_length=2, max_length=100, description="District")
    village: str = Field(..., min_length=2, max_length=100, description="Village/VPO (required)")
    pincode: str = Field(
        ..., min_length=6, max_length=10, description="Farm postal code (required)"
    )
    total_area_acres: float = Field(..., gt=0, description="Total farm area in acres")
    address_line: Optional[str] = Field(None, max_length=255, description="Address line (optional)")
    primary_soil_type: Optional[str] = Field(None, description="Primary soil type for the farm")
    irrigation_type: Optional[str] = Field(None, description="Primary irrigation type for the farm")
    nitrogen: Optional[float] = Field(None, ge=0, description="Nitrogen content (kg/ha)")
    phosphorus: Optional[float] = Field(None, ge=0, description="Phosphorus content (kg/ha)")
    potassium: Optional[float] = Field(None, ge=0, description="Potassium content (kg/ha)")
    ph_level: Optional[float] = Field(None, ge=0, le=14, description="pH level (0-14)")
    organic_carbon: Optional[float] = Field(None, ge=0, le=100, description="Organic carbon (%)")
    electrical_conductivity: Optional[float] = Field(None, ge=0, description="EC (dS/m)")
    sulfur: Optional[float] = Field(None, ge=0, description="Sulfur (ppm)")
    zinc: Optional[float] = Field(None, ge=0, description="Zinc (ppm)")
    iron: Optional[float] = Field(None, ge=0, description="Iron (ppm)")
    boron: Optional[float] = Field(None, ge=0, description="Boron (ppm)")

    @field_validator("name", "state", "district", "village", "address_line")
    @classmethod
    def sanitize_location_fields(cls, v: Optional[str]) -> Optional[str]:
        """Sanitize location text fields"""
        if v is None:
            return v
        return sanitize_input(v, allow_html=False)

    @field_validator("pincode")
    @classmethod
    def validate_pincode(cls, v: str) -> str:
        """Validate pincode format (6 digits for India)"""
        import re

        if not re.match(r"^\d{6}$", v):
            raise ValueError("Pincode must be 6 digits")
        return v

    @field_validator("total_area_acres")
    @classmethod
    def validate_total_area(cls, v: float) -> float:
        """Validate total area"""
        return NumericRangeValidator.validate_area(v, min_area=0.1, max_area=10000.0)

    @field_validator("primary_soil_type")
    @classmethod
    def validate_farm_soil_type(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        return validate_enum(v, EnumValidator.SOIL_TYPES, "primary_soil_type")

    @field_validator("irrigation_type")
    @classmethod
    def validate_farm_irrigation_type(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        return validate_enum(v, EnumValidator.IRRIGATION_TYPES, "irrigation_type")


class FarmCreate(FarmBase):
    """Farm creation schema with GPS coordinates"""

    latitude: Optional[float] = Field(
        None, ge=-90, le=90, description="Farm GPS latitude (optional)"
    )
    longitude: Optional[float] = Field(
        None, ge=-180, le=180, description="Farm GPS longitude (optional)"
    )
    plots: Optional[List[PlotCreate]] = Field(None, description="Initial plots to create")

    @field_validator("longitude")
    @classmethod
    def validate_coords(cls, v: Optional[float], info) -> Optional[float]:
        """Validate coordinates - both must be provided together or not at all"""
        values = info.data
        lat = values.get("latitude")
        lng = v

        # If one is provided, both must be provided
        if (lat is None) != (lng is None):
            raise ValueError("Both latitude and longitude must be provided together or not at all")

        # Validate both coordinates together
        validated_lat, validated_lng = validate_coordinates(lat, lng)
        return validated_lng


class FarmUpdate(BaseModel):
    """Farm update schema with address support"""

    name: Optional[str] = Field(None, min_length=1, max_length=200)
    state: Optional[str] = Field(None, min_length=2, max_length=100)
    district: Optional[str] = Field(None, min_length=2, max_length=100)
    village: Optional[str] = Field(None, min_length=2, max_length=100)
    pincode: Optional[str] = Field(None, min_length=6, max_length=10)
    total_area_acres: Optional[float] = Field(None, gt=0)
    latitude: Optional[float] = Field(None, ge=-90, le=90)
    longitude: Optional[float] = Field(None, ge=-180, le=180)
    address_line: Optional[str] = Field(None, max_length=255)
    primary_soil_type: Optional[str] = None
    irrigation_type: Optional[str] = None
    nitrogen: Optional[float] = Field(None, ge=0)
    phosphorus: Optional[float] = Field(None, ge=0)
    potassium: Optional[float] = Field(None, ge=0)
    ph_level: Optional[float] = Field(None, ge=0, le=14)
    organic_carbon: Optional[float] = Field(None, ge=0, le=100)
    electrical_conductivity: Optional[float] = Field(None, ge=0)
    sulfur: Optional[float] = Field(None, ge=0)
    zinc: Optional[float] = Field(None, ge=0)
    iron: Optional[float] = Field(None, ge=0)
    boron: Optional[float] = Field(None, ge=0)

    @field_validator("name", "state", "district", "village", "address_line")
    @classmethod
    def sanitize_location_fields(cls, v: Optional[str]) -> Optional[str]:
        """Sanitize location text fields"""
        if v is None:
            return v
        return sanitize_input(v, allow_html=False)

    @field_validator("pincode")
    @classmethod
    def validate_pincode(cls, v: Optional[str]) -> Optional[str]:
        """Validate pincode format"""
        if v is None:
            return v
        import re

        if not re.match(r"^\d{6}$", v):
            raise ValueError("Pincode must be 6 digits")
        return v

    @field_validator("total_area_acres")
    @classmethod
    def validate_total_area(cls, v: Optional[float]) -> Optional[float]:
        """Validate total area"""
        if v is None:
            return v
        return NumericRangeValidator.validate_area(v, min_area=0.1, max_area=10000.0)

    @field_validator("primary_soil_type")
    @classmethod
    def validate_farm_soil_type(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        return validate_enum(v, EnumValidator.SOIL_TYPES, "primary_soil_type")

    @field_validator("irrigation_type")
    @classmethod
    def validate_farm_irrigation_type(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        return validate_enum(v, EnumValidator.IRRIGATION_TYPES, "irrigation_type")


class FarmResponse(BaseModel):
    """Farm response schema with address fields"""

    id: int = Field(..., description="Farm ID")
    farmer_id: int = Field(..., description="Farmer user ID")
    name: str = Field(..., min_length=1, max_length=200, description="Farm name")
    state: str = Field(..., min_length=2, max_length=100, description="State")
    district: str = Field(..., min_length=2, max_length=100, description="District")
    village: str = Field(..., min_length=2, max_length=100, description="Village/VPO")
    pincode: Optional[str] = Field(None, description="Farm postal code (not stored in DB)")
    total_area_acres: float = Field(..., gt=0, description="Total farm area in acres")
    address_line: Optional[str] = Field(None, description="Address line")
    primary_soil_type: Optional[str] = Field(None, description="Primary soil type")
    irrigation_type: Optional[str] = Field(None, description="Primary irrigation type")
    latitude: Optional[float] = Field(None, description="Farm GPS latitude (optional)")
    longitude: Optional[float] = Field(None, description="Farm GPS longitude (optional)")
    is_active: bool = Field(..., description="Farm active status")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    nitrogen: Optional[float] = Field(None, description="Nitrogen content (kg/ha)")
    phosphorus: Optional[float] = Field(None, description="Phosphorus content (kg/ha)")
    potassium: Optional[float] = Field(None, description="Potassium content (kg/ha)")
    ph_level: Optional[float] = Field(None, description="pH level (0-14)")
    organic_carbon: Optional[float] = Field(None, description="Organic carbon (%)")
    electrical_conductivity: Optional[float] = Field(None, description="EC (dS/m)")
    sulfur: Optional[float] = Field(None, description="Sulfur (ppm)")
    zinc: Optional[float] = Field(None, description="Zinc (ppm)")
    iron: Optional[float] = Field(None, description="Iron (ppm)")
    boron: Optional[float] = Field(None, description="Boron (ppm)")

    model_config = ConfigDict(from_attributes=True)


class FarmDetailResponse(FarmResponse):
    """Detailed farm response with plots"""

    plots: List[PlotResponse] = Field(default_factory=list, description="Farm plots")

    model_config = ConfigDict(from_attributes=True)


class FarmListResponse(BaseModel):
    """Farm list response"""

    farms: List[FarmResponse] = Field(..., description="List of farms")
    total: int = Field(..., description="Total number of farms")


class PlotListResponse(BaseModel):
    """Plot list response"""

    plots: List[PlotResponse] = Field(..., description="List of plots")
    total: int = Field(..., description="Total number of plots")
