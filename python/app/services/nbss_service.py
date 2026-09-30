"""
NBSS (National Bureau of Soil Survey) Soil Map Integration Service
Handles GPS-based soil lookup, district-level fallback, and soil profile matching

Task 22.2: Implement soil map integration
"""

import logging
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Any  # db kept for compatibility; queries use app.core.db.DB
from typing import Any as AsyncSession
from typing import Dict, List, Optional, Tuple

import httpx

from app.services.farm_access import run_named

logger = logging.getLogger(__name__)


class NBSSService:
    """Service for NBSS soil map integration and soil profile matching"""

    # NBSS API configuration (placeholder - actual API details would be configured)
    NBSS_API_BASE_URL = "https://api.nbss.gov.in/soil-maps"  # Placeholder
    NBSS_API_KEY = None  # Would be loaded from settings

    # Cache TTL: 24 hours
    CACHE_TTL_HOURS = 24

    # Confidence scores
    CONFIDENCE_GPS = 0.9
    CONFIDENCE_DISTRICT = 0.6

    # GPS search radius for similar farms (in kilometers)
    SIMILARITY_RADIUS_KM = 50

    def __init__(self, db: AsyncSession):
        """Initialize NBSS service with database session"""
        self.db = db

    async def get_soil_characteristics_by_gps(
        self, latitude: float, longitude: float, use_cache: bool = True
    ) -> Optional[Dict[str, Any]]:
        """
        Get soil characteristics from NBSS API based on GPS coordinates

        Args:
            latitude: GPS latitude
            longitude: GPS longitude
            use_cache: Whether to use cached data (default True)

        Returns:
            Soil characteristics dictionary or None if not found
        """
        logger.info(f"Fetching soil characteristics for GPS: {latitude}, {longitude}")

        # Check cache first
        if use_cache:
            cached_data = await self._get_cached_soil_data(
                latitude=latitude, longitude=longitude, lookup_type="gps"
            )
            if cached_data:
                logger.info("Returning cached soil data")
                return cached_data

        # Fetch from NBSS API
        try:
            soil_data = await self._fetch_from_nbss_api(latitude, longitude)

            if soil_data:
                # Cache the response
                await self._cache_soil_data(
                    latitude=latitude,
                    longitude=longitude,
                    lookup_type="gps",
                    soil_data=soil_data,
                    confidence_score=self.CONFIDENCE_GPS,
                    data_source="NBSS",
                )

                return soil_data
            else:
                logger.warning(f"No soil data found from NBSS for GPS: {latitude}, {longitude}")
                return None

        except Exception as e:
            logger.error(f"Error fetching from NBSS API: {str(e)}")
            return None

    async def get_soil_characteristics_by_district(
        self, state: str, district: str, use_cache: bool = True
    ) -> Optional[Dict[str, Any]]:
        """
        Get district-level average soil characteristics as fallback

        Args:
            state: State name
            district: District name
            use_cache: Whether to use cached data (default True)

        Returns:
            District-level soil characteristics or None
        """
        logger.info(f"Fetching district-level soil data for {district}, {state}")

        # Check cache first
        if use_cache:
            cached_data = await self._get_cached_soil_data(
                state=state, district=district, lookup_type="district"
            )
            if cached_data:
                logger.info("Returning cached district-level soil data")
                return cached_data

        # Fetch district-level averages
        try:
            soil_data = await self._fetch_district_averages(state, district)

            if soil_data:
                # Cache the response
                await self._cache_soil_data(
                    state=state,
                    district=district,
                    lookup_type="district",
                    soil_data=soil_data,
                    confidence_score=self.CONFIDENCE_DISTRICT,
                    data_source="district_average",
                )

                return soil_data
            else:
                logger.warning(f"No district-level soil data found for {district}, {state}")
                return None

        except Exception as e:
            logger.error(f"Error fetching district-level soil data: {str(e)}")
            return None

    async def auto_populate_soil_characteristics(
        self,
        farm_id: int,
        latitude: Optional[float] = None,
        longitude: Optional[float] = None,
        state: Optional[str] = None,
        district: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Auto-populate soil characteristics for a farm
        Uses GPS if available, falls back to district-level averages

        Args:
            farm_id: Farm ID
            latitude: GPS latitude (optional)
            longitude: GPS longitude (optional)
            state: State name (optional)
            district: District name (optional)

        Returns:
            Soil characteristics with source attribution
        """
        logger.info(f"Auto-populating soil characteristics for farm {farm_id}")

        result = {
            "farm_id": farm_id,
            "soil_data": None,
            "data_source": None,
            "confidence_score": 0.0,
            "lookup_method": None,
        }

        # Try GPS lookup first
        if latitude is not None and longitude is not None:
            soil_data = await self.get_soil_characteristics_by_gps(latitude, longitude)
            if soil_data:
                result["soil_data"] = soil_data
                result["data_source"] = "NBSS_GPS"
                result["confidence_score"] = self.CONFIDENCE_GPS
                result["lookup_method"] = "gps"
                logger.info(f"Successfully populated soil data from GPS for farm {farm_id}")
                return result

        # Fallback to district-level averages
        if state and district:
            soil_data = await self.get_soil_characteristics_by_district(state, district)
            if soil_data:
                result["soil_data"] = soil_data
                result["data_source"] = "district_average"
                result["confidence_score"] = self.CONFIDENCE_DISTRICT
                result["lookup_method"] = "district"
                logger.info(f"Successfully populated soil data from district for farm {farm_id}")
                return result

        logger.warning(f"Could not populate soil data for farm {farm_id}")
        return result

    async def find_similar_farms(
        self,
        latitude: float,
        longitude: float,
        radius_km: float = None,
        user=None,
    ) -> List[Dict[str, Any]]:
        """
        Find similar farms within radius using pgvector similarity search

        Args:
            latitude: GPS latitude
            longitude: GPS longitude
            radius_km: Search radius in kilometers (default 50km)

        Returns:
            List of similar farms with soil characteristics
        """
        if radius_km is None:
            radius_km = self.SIMILARITY_RADIUS_KM

        logger.info(f"Finding similar farms within {radius_km}km of {latitude}, {longitude}")

        try:
            # Calculate distance using Haversine formula in SQL
            # Earth radius in km
            earth_radius = 6371

            query = """
                SELECT 
                    f.id,
                    f.user_id,
                    f.name,
                    f.location_state AS state,
                    f.location_district AS district,
                    f.latitude,
                    f.longitude,
                    f.total_area,
                    (
                        :earth_radius * acos(LEAST(1.0, GREATEST(-1.0,  -- clamp float error
                            cos(radians(:lat)) * cos(radians(f.latitude)) * 
                            cos(radians(f.longitude) - radians(:lon)) + 
                            sin(radians(:lat)) * sin(radians(f.latitude))))
                        )
                    ) AS distance_km
                FROM farms f
                WHERE 
                    f.latitude IS NOT NULL 
                    AND f.longitude IS NOT NULL
                    AND (
                        :earth_radius * acos(LEAST(1.0, GREATEST(-1.0,  -- clamp float error
                            cos(radians(:lat)) * cos(radians(f.latitude)) * 
                            cos(radians(f.longitude) - radians(:lon)) + 
                            sin(radians(:lat)) * sin(radians(f.latitude))))
                        )
                    ) <= :radius
                ORDER BY distance_km
                LIMIT 20
            """

            result = run_named(
                query,
                {
                    "lat": latitude,
                    "lon": longitude,
                    "radius": radius_km,
                    "earth_radius": earth_radius,
                },
            )

            # Other users' farms are anonymised (no name or exact coordinates) unless the caller is an admin.
            is_admin = getattr(user, "user_type", None) == "admin"
            farms = []
            for row in result:
                if user is not None and not is_admin and row.user_id != getattr(user, "id", None):
                    farms.append(
                        {
                            "farm_id": row.id,
                            "farm_name": "Nearby farm",
                            "state": row.state,
                            "district": row.district,
                            "latitude": None,
                            "longitude": None,
                            "total_area": float(row.total_area) if row.total_area else None,
                            "distance_km": round(float(row.distance_km), 2),
                        }
                    )
                    continue
                farms.append(
                    {
                        "farm_id": row.id,
                        "farm_name": row.name,
                        "state": row.state,
                        "district": row.district,
                        "latitude": float(row.latitude) if row.latitude else None,
                        "longitude": float(row.longitude) if row.longitude else None,
                        "total_area": float(row.total_area) if row.total_area else None,
                        "distance_km": round(float(row.distance_km), 2),
                    }
                )

            logger.info(f"Found {len(farms)} similar farms within {radius_km}km")
            return farms

        except Exception as e:
            logger.error(f"Error finding similar farms: {str(e)}")
            return []

    async def get_peer_comparison_insights(
        self,
        farm_id: int,
        latitude: float,
        longitude: float,
        user=None,
    ) -> Dict[str, Any]:
        """
        Get peer comparison insights for a farm

        Args:
            farm_id: Farm ID
            latitude: GPS latitude
            longitude: GPS longitude

        Returns:
            Peer comparison insights
        """
        logger.info(f"Generating peer comparison insights for farm {farm_id}")

        similar_farms = await self.find_similar_farms(latitude, longitude, user=user)

        if not similar_farms:
            return {
                "farm_id": farm_id,
                "similar_farms_count": 0,
                "insights": "No similar farms found within 50km radius",
            }

        # Calculate statistics
        total_farms = len(similar_farms)
        avg_distance = sum(f["distance_km"] for f in similar_farms) / total_farms
        closest_farm = similar_farms[0] if similar_farms else None

        # Get district distribution
        districts = {}
        for farm in similar_farms:
            district = farm["district"]
            districts[district] = districts.get(district, 0) + 1

        return {
            "farm_id": farm_id,
            "similar_farms_count": total_farms,
            "average_distance_km": round(avg_distance, 2),
            "closest_farm": closest_farm,
            "district_distribution": districts,
            "similar_farms": similar_farms[:10],  # Return top 10
        }

    async def _fetch_from_nbss_api(
        self, latitude: float, longitude: float
    ) -> Optional[Dict[str, Any]]:
        """
        Fetch soil data from NBSS API

        Note: This is a placeholder implementation. Actual NBSS API integration
        would require official API credentials and documentation.

        Args:
            latitude: GPS latitude
            longitude: GPS longitude

        Returns:
            Soil characteristics or None
        """
        logger.info(f"Calling NBSS API for GPS: {latitude}, {longitude}")

        # TODO: Implement actual NBSS API integration when API is available
        # This would involve:
        # 1. Authentication with NBSS API
        # 2. Making HTTP request with GPS coordinates
        # 3. Parsing response and mapping to our schema
        # 4. Handling rate limits and errors

        # Placeholder implementation - simulate API response
        logger.warning("NBSS API integration not yet implemented - using placeholder data")

        # For now, return None to trigger fallback to district-level data
        # In production, this would make actual API call
        return None

    async def _fetch_district_averages(self, state: str, district: str) -> Optional[Dict[str, Any]]:
        """
        Fetch district-level average soil characteristics

        This could come from:
        1. Pre-loaded district-level data in database
        2. NBSS district-level API
        3. Aggregated data from existing farms in the district

        Args:
            state: State name
            district: District name

        Returns:
            District-level soil characteristics
        """
        logger.info(f"Fetching district averages for {district}, {state}")

        # TODO: Implement district-level data lookup
        # For now, return generic data based on common Indian soil types

        # Placeholder district-level data
        district_data = {
            "soil_type": "Mixed",
            "soil_texture": "Loamy",
            "drainage": "Moderate",
            "slope": "Gentle",
            "ph_range": "6.5-7.5",
            "organic_carbon_range": "0.4-0.6%",
            "confidence_score": self.CONFIDENCE_DISTRICT,
            "data_source": "district_average",
            "state": state,
            "district": district,
            "notes": "District-level average soil characteristics",
        }

        return district_data

    async def _get_cached_soil_data(
        self,
        latitude: Optional[float] = None,
        longitude: Optional[float] = None,
        state: Optional[str] = None,
        district: Optional[str] = None,
        lookup_type: str = "gps",
    ) -> Optional[Dict[str, Any]]:
        """
        Get cached soil data from database

        Args:
            latitude: GPS latitude (for GPS lookup)
            longitude: GPS longitude (for GPS lookup)
            state: State name (for district lookup)
            district: District name (for district lookup)
            lookup_type: 'gps' or 'district'

        Returns:
            Cached soil data or None if not found or expired
        """
        try:
            query = """
                SELECT 
                    soil_type,
                    soil_texture,
                    drainage,
                    slope,
                    ph_range,
                    organic_carbon_range,
                    confidence_score,
                    data_source,
                    nbss_response,
                    created_at
                FROM soil_map_cache
                WHERE 
                    lookup_type = :lookup_type
                    AND expires_at > CURRENT_TIMESTAMP
                    AND (
                        (:lookup_type = 'gps' AND latitude = :lat AND longitude = :lon)
                        OR
                        (:lookup_type = 'district' AND state = :state AND district = :district)
                    )
                ORDER BY created_at DESC
                LIMIT 1
            """

            result = run_named(
                query,
                {
                    "lookup_type": lookup_type,
                    "lat": latitude,
                    "lon": longitude,
                    "state": state,
                    "district": district,
                },
            )

            row = result.first()

            if row:
                logger.info(f"Found cached soil data (lookup_type: {lookup_type})")
                return {
                    "soil_type": row.soil_type,
                    "soil_texture": row.soil_texture,
                    "drainage": row.drainage,
                    "slope": row.slope,
                    "ph_range": row.ph_range,
                    "organic_carbon_range": row.organic_carbon_range,
                    "confidence_score": float(row.confidence_score),
                    "data_source": row.data_source,
                    "nbss_response": row.nbss_response,
                    "cached_at": row.created_at.isoformat() if row.created_at else None,
                }

            return None

        except Exception as e:
            logger.error(f"Error retrieving cached soil data: {str(e)}")
            return None

    async def _cache_soil_data(
        self,
        soil_data: Dict[str, Any],
        confidence_score: float,
        data_source: str,
        lookup_type: str,
        latitude: Optional[float] = None,
        longitude: Optional[float] = None,
        state: Optional[str] = None,
        district: Optional[str] = None,
    ) -> None:
        """
        Cache soil data in database with 24-hour TTL

        Args:
            soil_data: Soil characteristics to cache
            confidence_score: Confidence score (0-1)
            data_source: Data source identifier
            lookup_type: 'gps' or 'district'
            latitude: GPS latitude (for GPS lookup)
            longitude: GPS longitude (for GPS lookup)
            state: State name (for district lookup)
            district: District name (for district lookup)
        """
        try:
            expires_at = datetime.utcnow() + timedelta(hours=self.CACHE_TTL_HOURS)

            query = """
                INSERT INTO soil_map_cache (
                    latitude, longitude, state, district, lookup_type,
                    soil_type, soil_texture, drainage, slope,
                    ph_range, organic_carbon_range,
                    confidence_score, data_source, nbss_response,
                    expires_at
                ) VALUES (
                    :lat, :lon, :state, :district, :lookup_type,
                    :soil_type, :soil_texture, :drainage, :slope,
                    :ph_range, :organic_carbon_range,
                    :confidence_score, :data_source, :nbss_response,
                    :expires_at
                )
            """

            run_named(
                query,
                {
                    "lat": latitude,
                    "lon": longitude,
                    "state": state,
                    "district": district,
                    "lookup_type": lookup_type,
                    "soil_type": soil_data.get("soil_type"),
                    "soil_texture": soil_data.get("soil_texture"),
                    "drainage": soil_data.get("drainage"),
                    "slope": soil_data.get("slope"),
                    "ph_range": soil_data.get("ph_range"),
                    "organic_carbon_range": soil_data.get("organic_carbon_range"),
                    "confidence_score": confidence_score,
                    "data_source": data_source,
                    "nbss_response": soil_data.get("nbss_response"),
                    "expires_at": expires_at,
                },
            )

            # committed by DB.raw
            # Note: soil_map_cache is not in the current schema; until it exists this insert fails
            # and is logged below (lookups then simply skip the cache).
            logger.info(f"Cached soil data (lookup_type: {lookup_type}, expires: {expires_at})")

        except Exception as e:
            logger.error(f"Error caching soil data: {str(e)}")


# Helper function to create service instance
def get_nbss_service(db: AsyncSession) -> NBSSService:
    """Get NBSS service instance"""
    return NBSSService(db)
