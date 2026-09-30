"""
Address Management Service

Handles address operations including validation, auto-fill from pincode,
and GPS coordinate management.
"""

import logging
from typing import Optional

from app.schemas.address import (
    AddressAutoFillResponse,
    AddressBase,
    DeliveryAddressUpdate,
    FarmAddressUpdate,
    LivestockAddressUpdate,
    UserAddressUpdate,
)
from app.services.pincode_lookup_service import PincodeLookupService

logger = logging.getLogger(__name__)


class AddressService:
    """Service for address management operations"""

    def __init__(self, redis_client=None):
        """
        Initialize address service

        Args:
            redis_client: Optional Redis client for caching
        """
        self.pincode_service = PincodeLookupService(redis_client)

    async def auto_fill_from_pincode(self, pincode: str) -> Optional[AddressAutoFillResponse]:
        """
        Auto-fill address information from pincode

        Args:
            pincode: 6-digit Indian pincode

        Returns:
            AddressAutoFillResponse with state, district, and villages
            None if pincode not found
        """
        lookup_result = await self.pincode_service.lookup_pincode(pincode)

        if not lookup_result:
            logger.warning(f"Auto-fill failed for pincode {pincode}")
            return None

        return AddressAutoFillResponse(
            pincode=lookup_result["pincode"],
            state=lookup_result["state"],
            district=lookup_result["district"],
            villages=lookup_result["villages"],
        )

    async def validate_address(self, address: AddressBase) -> tuple[bool, Optional[str]]:
        """
        Validate address against pincode data

        Args:
            address: AddressBase object to validate

        Returns:
            Tuple of (is_valid, error_message)
        """
        # Validate GPS coordinates consistency
        if (address.latitude is None) != (address.longitude is None):
            return False, "Both latitude and longitude must be provided together or not at all"

        # Validate pincode format
        if not address.pincode or len(address.pincode) != 6:
            return False, "Pincode must be 6 digits"

        # Validate against pincode API
        is_valid = await self.pincode_service.validate_address(
            pincode=address.pincode,
            state=address.state,
            district=address.district,
            village=address.village,
        )

        if not is_valid:
            return (
                False,
                "Address does not match pincode data. Please verify state, district, and village.",
            )

        return True, None

    def has_gps_coordinates(self, address: AddressBase) -> bool:
        """
        Check if address has GPS coordinates

        Args:
            address: AddressBase object

        Returns:
            True if both latitude and longitude are present
        """
        return address.latitude is not None and address.longitude is not None

    def format_full_address(self, address: AddressBase) -> str:
        """
        Format complete address as string

        Args:
            address: AddressBase object

        Returns:
            Formatted address string
        """
        parts = []

        if address.address_line:
            parts.append(address.address_line)

        parts.append(address.village)
        parts.append(address.district)
        parts.append(address.state)
        parts.append(address.pincode)

        return ", ".join(parts)

    def calculate_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """
        Calculate distance between two GPS coordinates using Haversine formula

        Args:
            lat1: Latitude of first point
            lon1: Longitude of first point
            lat2: Latitude of second point
            lon2: Longitude of second point

        Returns:
            Distance in kilometers
        """
        from math import atan2, cos, radians, sin, sqrt

        # Earth radius in kilometers
        R = 6371.0

        # Convert to radians
        lat1_rad = radians(lat1)
        lon1_rad = radians(lon1)
        lat2_rad = radians(lat2)
        lon2_rad = radians(lon2)

        # Haversine formula
        dlat = lat2_rad - lat1_rad
        dlon = lon2_rad - lon1_rad

        a = sin(dlat / 2) ** 2 + cos(lat1_rad) * cos(lat2_rad) * sin(dlon / 2) ** 2
        c = 2 * atan2(sqrt(a), sqrt(1 - a))

        distance = R * c
        return distance

    async def find_nearby_locations(
        self, latitude: float, longitude: float, max_distance_km: float, locations: list[dict]
    ) -> list[dict]:
        """
        Find locations within specified distance from coordinates

        Args:
            latitude: Center point latitude
            longitude: Center point longitude
            max_distance_km: Maximum distance in kilometers
            locations: List of location dicts with 'latitude' and 'longitude' keys

        Returns:
            List of locations within distance, sorted by distance
        """
        nearby = []

        for location in locations:
            if "latitude" not in location or "longitude" not in location:
                continue

            if location["latitude"] is None or location["longitude"] is None:
                continue

            distance = self.calculate_distance(
                latitude, longitude, location["latitude"], location["longitude"]
            )

            if distance <= max_distance_km:
                location_with_distance = {**location, "distance_km": distance}
                nearby.append(location_with_distance)

        # Sort by distance
        nearby.sort(key=lambda x: x["distance_km"])

        return nearby

    def extract_address_fields(self, data: dict, prefix: str = "") -> dict:
        """
        Extract address fields from dictionary with optional prefix

        Args:
            data: Dictionary containing address fields
            prefix: Optional prefix for field names (e.g., "delivery_")

        Returns:
            Dictionary with address fields
        """
        fields = [
            "latitude",
            "longitude",
            "pincode",
            "state",
            "district",
            "village",
            "address_line",
        ]

        address = {}
        for field in fields:
            key = f"{prefix}{field}" if prefix else field
            if key in data:
                address[field] = data[key]

        return address
