"""
Soil Map API Endpoints
Provides GPS-based soil lookup, district-level fallback, and soil profile matching

Task 22.2: Implement soil map integration
"""

import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.services.farm_access import farm_for_user
from app.services.nbss_service import NBSSService, get_nbss_service

logger = logging.getLogger(__name__)

from app.core.auth import get_current_active_user

router = APIRouter(
    prefix="/soil-maps", tags=["soil-maps"], dependencies=[Depends(get_current_active_user)]
)


# Request/Response Models
class SoilCharacteristicsResponse(BaseModel):
    """Soil characteristics response"""

    soil_type: Optional[str] = Field(None, description="Soil classification")
    soil_texture: Optional[str] = Field(None, description="Soil texture")
    drainage: Optional[str] = Field(None, description="Drainage characteristics")
    slope: Optional[str] = Field(None, description="Slope characteristics")
    ph_range: Optional[str] = Field(None, description="pH range")
    organic_carbon_range: Optional[str] = Field(None, description="Organic carbon range")
    confidence_score: float = Field(..., description="Confidence score 0-1")
    data_source: str = Field(..., description="Data source identifier")
    cached_at: Optional[str] = Field(None, description="Cache timestamp")


class AutoPopulateRequest(BaseModel):
    """Request to auto-populate soil characteristics"""

    farm_id: int = Field(..., description="Farm ID")
    latitude: Optional[float] = Field(None, description="GPS latitude")
    longitude: Optional[float] = Field(None, description="GPS longitude")
    state: Optional[str] = Field(None, description="State name")
    district: Optional[str] = Field(None, description="District name")


class AutoPopulateResponse(BaseModel):
    """Response from auto-populate"""

    farm_id: int
    soil_data: Optional[SoilCharacteristicsResponse]
    data_source: Optional[str]
    confidence_score: float
    lookup_method: Optional[str]


class SimilarFarm(BaseModel):
    """Similar farm information"""

    farm_id: int
    farm_name: str
    state: str
    district: str
    latitude: Optional[float]
    longitude: Optional[float]
    total_area: Optional[float]
    distance_km: float


class PeerComparisonResponse(BaseModel):
    """Peer comparison insights"""

    farm_id: int
    similar_farms_count: int
    average_distance_km: Optional[float] = None
    closest_farm: Optional[SimilarFarm] = None
    district_distribution: dict
    similar_farms: List[SimilarFarm]


@router.get("", response_model=Dict[str, Any])
async def get_soil_map_root():
    """Registry alias for soil maps root"""
    return {
        "status": "success",
        "message": "Soil mapping system operational",
        "features": ["gps_lookup", "district_fallback", "auto_populate"],
    }


# API Endpoints


@router.get("/gps", response_model=SoilCharacteristicsResponse)
async def get_soil_by_gps(
    latitude: float = Query(..., description="GPS latitude", ge=-90, le=90),
    longitude: float = Query(..., description="GPS longitude", ge=-180, le=180),
    use_cache: bool = Query(True, description="Use cached data if available"),
    db: AsyncSession = Depends(get_db),
):
    """
    Get soil characteristics based on GPS coordinates

    Uses NBSS soil maps API to retrieve soil data for specific location.
    Results are cached for 24 hours.

    **Validation Metrics (AC7):**
    - NBSS integration success rate > 90%
    - GPS lookup accuracy within 1km
    - Response time < 5 seconds
    """
    logger.info(f"GET /soil-maps/gps - lat: {latitude}, lon: {longitude}")

    try:
        service = get_nbss_service(db)
        soil_data = await service.get_soil_characteristics_by_gps(
            latitude=latitude, longitude=longitude, use_cache=use_cache
        )

        if not soil_data:
            raise HTTPException(
                status_code=404, detail="No soil data found for the specified GPS coordinates"
            )

        return SoilCharacteristicsResponse(**soil_data)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in get_soil_by_gps: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error retrieving soil data: {str(e)}")


@router.get("/district", response_model=SoilCharacteristicsResponse)
async def get_soil_by_district(
    state: str = Query(..., description="State name"),
    district: str = Query(..., description="District name"),
    use_cache: bool = Query(True, description="Use cached data if available"),
    db: AsyncSession = Depends(get_db),
):
    """
    Get district-level average soil characteristics (fallback)

    Provides district-level soil averages when GPS coordinates are unavailable.
    Results are cached for 24 hours.

    **Validation Metrics (AC7):**
    - Fallback accuracy > 80% vs manual entry
    - Response time < 5 seconds
    """
    logger.info(f"GET /soil-maps/district - state: {state}, district: {district}")

    try:
        service = get_nbss_service(db)
        soil_data = await service.get_soil_characteristics_by_district(
            state=state, district=district, use_cache=use_cache
        )

        if not soil_data:
            raise HTTPException(
                status_code=404, detail=f"No soil data found for {district}, {state}"
            )

        return SoilCharacteristicsResponse(**soil_data)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in get_soil_by_district: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Error retrieving district soil data: {str(e)}"
        )


@router.post("/auto-populate", response_model=AutoPopulateResponse)
async def auto_populate_soil_characteristics(
    request: AutoPopulateRequest, db: AsyncSession = Depends(get_db)
):
    """
    Auto-populate soil characteristics for a farm

    Tries GPS lookup first, falls back to district-level averages if GPS unavailable.
    Implements confidence scoring (GPS: 0.9, district: 0.6).

    **Validation Metrics (AC7):**
    - NBSS integration success rate > 90%
    - GPS lookup accuracy within 1km
    - Fallback accuracy > 80% vs manual entry
    - Response time < 5 seconds
    """
    logger.info(f"POST /soil-maps/auto-populate - farm_id: {request.farm_id}")

    try:
        service = get_nbss_service(db)
        result = await service.auto_populate_soil_characteristics(
            farm_id=request.farm_id,
            latitude=request.latitude,
            longitude=request.longitude,
            state=request.state,
            district=request.district,
        )

        # Convert soil_data to response model if present
        if result["soil_data"]:
            result["soil_data"] = SoilCharacteristicsResponse(**result["soil_data"])

        return AutoPopulateResponse(**result)

    except Exception as e:
        logger.error(f"Error in auto_populate_soil_characteristics: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error auto-populating soil data: {str(e)}")


@router.get("/similar-farms", response_model=List[SimilarFarm])
async def find_similar_farms(
    latitude: float = Query(..., description="GPS latitude", ge=-90, le=90),
    longitude: float = Query(..., description="GPS longitude", ge=-180, le=180),
    radius_km: float = Query(50, description="Search radius in kilometers", ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    """
    Find similar farms within radius using spatial search

    Uses Haversine formula to find farms within specified radius.
    Useful for peer comparison and benchmarking.

    **Default radius:** 50km
    """
    logger.info(
        f"GET /soil-maps/similar-farms - lat: {latitude}, lon: {longitude}, radius: {radius_km}km"
    )

    try:
        service = get_nbss_service(db)
        similar_farms = await service.find_similar_farms(
            latitude=latitude,
            longitude=longitude,
            radius_km=radius_km,
            user=current_user,
        )

        return [SimilarFarm(**farm) for farm in similar_farms]

    except Exception as e:
        logger.error(f"Error in find_similar_farms: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error finding similar farms: {str(e)}")


@router.get("/peer-comparison/{farm_id}", response_model=PeerComparisonResponse)
async def get_peer_comparison_insights(
    farm_id: int,
    latitude: float = Query(..., description="GPS latitude", ge=-90, le=90),
    longitude: float = Query(..., description="GPS longitude", ge=-180, le=180),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    """
    Get peer comparison insights for a farm

    Provides insights about similar farms within 50km radius including:
    - Number of similar farms
    - Average distance
    - Closest farm
    - District distribution
    - Top 10 similar farms
    """
    logger.info(f"GET /soil-maps/peer-comparison/{farm_id}")
    try:
        farm_for_user(farm_id, current_user)  # owner check (raw SQL); someone else's farm is 404
    except LookupError:
        raise HTTPException(status_code=404, detail="Farm not found")

    try:
        service = get_nbss_service(db)
        insights = await service.get_peer_comparison_insights(
            farm_id=farm_id,
            latitude=latitude,
            longitude=longitude,
            user=current_user,
        )

        # Convert similar farms to response models
        if "similar_farms" in insights:
            insights["similar_farms"] = [SimilarFarm(**farm) for farm in insights["similar_farms"]]

        if "closest_farm" in insights and insights["closest_farm"]:
            insights["closest_farm"] = SimilarFarm(**insights["closest_farm"])

        return PeerComparisonResponse(**insights)

    except Exception as e:
        logger.error(f"Error in get_peer_comparison_insights: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Error generating peer comparison insights: {str(e)}"
        )


@router.delete("/cache/clear")
async def clear_expired_cache(db: AsyncSession = Depends(get_db)):
    """
    Clear expired cache entries

    Removes soil map cache entries that have exceeded 24-hour TTL.
    This endpoint can be called manually or scheduled as a cron job.
    """
    logger.info("DELETE /soil-maps/cache/clear")

    try:
        from sqlalchemy import text

        query = text("""
            DELETE FROM soil_map_cache
            WHERE expires_at <= CURRENT_TIMESTAMP
        """)

        result = await db.execute(query)
        await db.commit()

        deleted_count = result.rowcount
        logger.info(f"Cleared {deleted_count} expired cache entries")

        return {"message": "Expired cache entries cleared", "deleted_count": deleted_count}

    except Exception as e:
        logger.error(f"Error clearing cache: {str(e)}")
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Error clearing cache: {str(e)}")
