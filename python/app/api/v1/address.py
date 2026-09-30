"""
Address Management API Endpoints

Provides endpoints for pincode lookup, address auto-fill, and validation.
"""

import logging
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import AddressSvc
from app.schemas.address import AddressAutoFillRequest, AddressAutoFillResponse, AddressBase
from app.services.address_service import AddressService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/address", tags=["address"])


# Removed helper-function dependency injection to enable direct cmd+click to class definition


@router.post("/auto-fill", response_model=AddressAutoFillResponse)
async def auto_fill_address(request: AddressAutoFillRequest, service: AddressSvc):
    """
    Auto-fill address information from pincode

    Looks up state, district, and villages for the given pincode
    using the India Post pincode API (https://api.postalpincode.in).

    - **pincode**: 6-digit Indian postal code

    Returns state, district, and list of villages/VPOs.
    """
    result = await service.auto_fill_from_pincode(request.pincode)

    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Pincode {request.pincode} not found. Please verify the pincode.",
        )

    return result


@router.post("/validate", response_model=dict)
async def validate_address(address: AddressBase, service: AddressSvc):
    """
    Validate address against pincode data

    Checks that state, district, and village match the pincode.
    Also validates GPS coordinate consistency.

    Returns validation result with error message if invalid.
    """
    is_valid, error_message = await service.validate_address(address)

    if not is_valid:
        return {"valid": False, "error": error_message}

    return {
        "valid": True,
        "message": "Address is valid",
        "has_gps": service.has_gps_coordinates(address),
        "formatted_address": service.format_full_address(address),
    }


@router.get("/pincode/{pincode}", response_model=AddressAutoFillResponse)
async def lookup_pincode(pincode: str, service: AddressSvc):
    """
    Look up address information for a pincode

    Alternative endpoint for pincode lookup using GET method.

    - **pincode**: 6-digit Indian postal code

    Returns state, district, and list of villages/VPOs.
    """
    if len(pincode) != 6 or not pincode.isdigit():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Pincode must be 6 digits"
        )

    result = await service.auto_fill_from_pincode(pincode)

    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Pincode {pincode} not found"
        )

    return result


@router.post("/distance", response_model=dict)
async def calculate_distance(
    lat1: float, lon1: float, lat2: float, lon2: float, service: AddressSvc
):
    """
    Calculate distance between two GPS coordinates

    Uses Haversine formula to calculate great-circle distance.

    - **lat1**: Latitude of first point
    - **lon1**: Longitude of first point
    - **lat2**: Latitude of second point
    - **lon2**: Longitude of second point

    Returns distance in kilometers.
    """
    distance = service.calculate_distance(lat1, lon1, lat2, lon2)

    return {"distance_km": round(distance, 2), "distance_miles": round(distance * 0.621371, 2)}
