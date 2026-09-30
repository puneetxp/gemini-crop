"""
Pincode Lookup Service

Integrates with the India Post pincode API (https://api.postalpincode.in) to
auto-fill address information based on Indian postal codes.

The previous provider, https://pincode.deno.dev, stopped serving when Deno
Deploy Classic was sunset on 2026-07-20 (every lookup returned 404). The parser
still accepts that provider's flat response shape.
"""

import logging
from datetime import timedelta
from typing import Optional

import httpx

logger = logging.getLogger(__name__)


class PincodeLookupService:
    """Service for looking up address information from pincode"""

    PINCODE_API_URL = "https://api.postalpincode.in/pincode"
    # Sunset 2026-07-20; kept for reference only, no longer called.
    LEGACY_PINCODE_API_URL = "https://pincode.deno.dev"
    # India Post regularly takes 2-5s to answer.
    TIMEOUT_SECONDS = 10
    CACHE_TTL_DAYS = 30

    def __init__(self, redis_client=None):
        """
        Initialize pincode lookup service

        Args:
            redis_client: Optional Redis client for caching
        """
        self.redis_client = redis_client
        self.cache_ttl = timedelta(days=self.CACHE_TTL_DAYS)

    async def lookup_pincode(self, pincode: str) -> Optional[dict]:
        """
        Look up address information for a pincode

        Args:
            pincode: 6-digit Indian pincode

        Returns:
            Dictionary with state, district, and list of villages/VPOs
            None if pincode not found or API error
        """
        # Check cache first
        if self.redis_client:
            cached_data = await self._get_from_cache(pincode)
            if cached_data:
                logger.info(f"Pincode {pincode} found in cache")
                return cached_data

        # Fetch from API
        try:
            async with httpx.AsyncClient(timeout=self.TIMEOUT_SECONDS) as client:
                response = await client.get(f"{self.PINCODE_API_URL}/{pincode}")

                if response.status_code == 200:
                    data = response.json()

                    if not data or len(data) == 0:
                        logger.warning(f"No data found for pincode {pincode}")
                        return None

                    result = self._parse_api_response(data)

                    if not result:
                        logger.warning(
                            f"No data found for pincode {pincode}: {str(data)[:200]}"
                        )
                        return None

                    # Cache the result
                    if self.redis_client:
                        await self._save_to_cache(pincode, result)

                    logger.info(f"Successfully looked up pincode {pincode}")
                    return result

                # Log the upstream body so a dead or moved provider is visible
                # (not just "not found").
                body = (getattr(response, "text", "") or "")[:200]
                if response.status_code == 404:
                    logger.warning(
                        f"Pincode {pincode} not found (404 from {self.PINCODE_API_URL}): {body}"
                    )
                else:
                    logger.error(
                        f"Pincode API {self.PINCODE_API_URL} returned status "
                        f"{response.status_code} for {pincode}: {body}"
                    )
                return None

        except httpx.TimeoutException:
            logger.error(f"Timeout looking up pincode {pincode}")
            return None
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error looking up pincode {pincode}: {e}")
            return None
        except httpx.RequestError as e:
            logger.error(f"Request error looking up pincode {pincode}: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error looking up pincode {pincode}: {e}")
            return None

    def _parse_api_response(self, data: list) -> Optional[dict]:
        """
        Parse API response into standardized format

        Accepts both shapes:
        - India Post: [{"Status": "Success", "PostOffice": [{"Name", "District", "State", "Pincode"}, ...]}]
        - legacy flat list: [{"pincode", "state", "district", "vpo"}, ...]

        Returns:
            Dictionary with state, district, and villages list, or None if empty
        """
        if not data or len(data) == 0:
            return None

        first = data[0] if isinstance(data, list) else data
        if isinstance(first, dict) and "PostOffice" in first:
            offices = first.get("PostOffice") or []
            if first.get("Status") != "Success" or not offices:
                return None
            return {
                "pincode": offices[0].get("Pincode", ""),
                "state": offices[0].get("State", ""),
                "district": offices[0].get("District", ""),
                "villages": sorted({o["Name"] for o in offices if o.get("Name")}),
            }

        # Extract unique state and district (should be same for all entries)
        state = data[0].get("state", "")
        district = data[0].get("district", "")
        pincode = data[0].get("pincode", "")

        # Extract all unique villages/VPOs
        villages = list(set([entry.get("vpo", "") for entry in data if entry.get("vpo")]))

        return {"pincode": pincode, "state": state, "district": district, "villages": villages}

    async def _get_from_cache(self, pincode: str) -> Optional[dict]:
        """Get pincode data from Redis cache"""
        try:
            import json

            cache_key = f"pincode:{pincode}"
            cached = await self.redis_client.get(cache_key)
            if cached:
                return json.loads(cached)
        except Exception as e:
            logger.error(f"Error reading from cache: {e}")
        return None

    async def _save_to_cache(self, pincode: str, data: dict) -> None:
        """Save pincode data to Redis cache"""
        try:
            import json

            cache_key = f"pincode:{pincode}"
            await self.redis_client.setex(
                cache_key, int(self.cache_ttl.total_seconds()), json.dumps(data)
            )
        except Exception as e:
            logger.error(f"Error saving to cache: {e}")

    async def validate_address(self, pincode: str, state: str, district: str, village: str) -> bool:
        """
        Validate that address components match pincode data

        Args:
            pincode: 6-digit pincode
            state: State name
            district: District name
            village: Village/VPO name

        Returns:
            True if address is valid, False otherwise
        """
        lookup_result = await self.lookup_pincode(pincode)

        if not lookup_result:
            logger.warning(f"Cannot validate address - pincode {pincode} lookup failed")
            return False

        # Case-insensitive comparison
        state_match = lookup_result["state"].lower() == state.lower()
        district_match = lookup_result["district"].lower() == district.lower()

        # We relax the village matching constraint because demo data and unlisted villages
        # should still be registerable if the Pincode, State & District are valid.
        # village_match = any(
        #     v.lower() == village.lower()
        #     for v in lookup_result['villages']
        # )
        village_match = True

        if not state_match:
            logger.warning(
                f"State mismatch for pincode {pincode}: {state} != {lookup_result['state']}"
            )
        if not district_match:
            logger.warning(
                f"District mismatch for pincode {pincode}: {district} != {lookup_result['district']}"
            )
        # if not village_match:
        #     logger.warning(f"Village {village} not found in pincode {pincode} villages")

        return state_match and district_match and village_match
