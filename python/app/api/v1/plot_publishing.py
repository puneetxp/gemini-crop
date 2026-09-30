"""
Plot Publishing API endpoints
Enables farmers to publish analyzed plots to marketplace for advance reservations

Task 27.1: Plot publishing API
"""

from __future__ import annotations

from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import get_current_user
from app.core.database import get_db
from app.services.farm_access import fetch_all, plot_for_user
from app.services.plot_publishing_service import PlotPublishingService


def _user_id(current_user):
    """current_user is an app.orm.user.User object (older code treated it as a dict with 'user_id')."""
    if isinstance(current_user, dict):
        return current_user.get("id", current_user.get("user_id"))
    return getattr(current_user, "id", None)


router = APIRouter(prefix="/plot-publishing", tags=["plot-publishing"])


class PlotPublishRequest(BaseModel):
    """Request model for publishing a plot to marketplace"""

    crop_name: str = Field(..., description="Selected crop name", min_length=1, max_length=255)
    crop_variety: str = Field(..., description="Crop variety", min_length=1, max_length=255)
    expected_harvest_date: str = Field(
        ..., description="Expected harvest date (ISO format: YYYY-MM-DD)"
    )
    quantity_quintals: float = Field(..., description="Estimated quantity in quintals", gt=0)
    quality_grade: str = Field(..., description="Quality grade (A/B/C)", pattern="^[ABC]$")
    price_per_quintal: float = Field(..., description="Asking price per quintal in ₹", gt=0)

    class Config:
        json_schema_extra = {
            "example": {
                "crop_name": "Rice",
                "crop_variety": "Basmati 1121",
                "expected_harvest_date": "2024-10-15",
                "quantity_quintals": 50.0,
                "quality_grade": "A",
                "price_per_quintal": 2500.0,
            }
        }


class PlotPublishResponse(BaseModel):
    """Response model for published plot"""

    listing_id: int
    plot_id: int
    plot_name: str
    status: str
    created_at: str
    crop_details: dict
    plot_characteristics: dict
    ai_predictions: dict
    farmer_contact: dict
    offering_terms: dict


@router.post("/publish")
async def publish_plot_alias(
    plot_id: int = Query(..., description="Plot ID"),
    request: PlotPublishRequest = None,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Registry alias for publish plot"""
    return await publish_plot_to_marketplace(plot_id, request, db, current_user)


@router.get("/listings")
async def get_plot_listings_alias(
    plot_id: int = Query(..., description="Plot ID"),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Registry alias for plot listings"""
    return await get_plot_listings(plot_id, db, current_user)


@router.post(
    "/{plot_id}/publish", response_model=PlotPublishResponse, status_code=status.HTTP_201_CREATED
)
async def publish_plot_to_marketplace(
    plot_id: int,
    request: PlotPublishRequest,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Publish a plot to marketplace for advance reservations

    This endpoint:
    1. Validates plot ownership and details
    2. Accepts crop selection, harvest date, quantity, quality grade, and pricing
    3. Generates AI predictions (yield confidence, quality confidence, harvest date range)
    4. Includes plot characteristics (location, area, soil type, irrigation, soil health score)
    5. Creates marketplace listing with status "published"
    6. Makes listing available for buyer reservations

    **Request Body:**
    - crop_name: Selected crop name (e.g., "Rice", "Wheat", "Cotton")
    - crop_variety: Specific variety (e.g., "Basmati 1121", "HD-2967")
    - expected_harvest_date: Expected harvest date in ISO format (YYYY-MM-DD)
    - quantity_quintals: Estimated quantity in quintals (1 quintal = 100 kg)
    - quality_grade: Expected quality grade (A/B/C)
    - price_per_quintal: Asking price per quintal in ₹

    **Response includes:**
    - listing_id: Unique marketplace listing ID
    - crop_details: Crop information, harvest date, quantity, quality, pricing
    - plot_characteristics: Location, area, soil type, irrigation, soil health
    - ai_predictions: Yield confidence, quality confidence, harvest date range
    - farmer_contact: Phone and email for buyer communication
    - offering_terms: Pricing, total value, advance booking availability

    **AI Predictions:**
    - yield_confidence: Confidence in yield prediction (0-1 scale)
    - quality_confidence: Confidence in quality grade (0-1 scale)
    - harvest_date_range: Predicted harvest window (±7-10 days)
    - suitability_score: Overall crop suitability for this plot (0-10)
    - risk_level: Risk assessment (low/medium/high)

    **Validates:**
    - Requirements AC7 (Smart Land Plot Management)
    - Plot ownership by current user
    - Valid crop and quality grade
    - Reasonable harvest date and quantity

    **Example:**
    ```
    POST /plots/123/publish
    {
      "crop_name": "Rice",
      "crop_variety": "Basmati 1121",
      "expected_harvest_date": "2024-10-15",
      "quantity_quintals": 50.0,
      "quality_grade": "A",
      "price_per_quintal": 2500.0
    }
    ```
    """
    try:
        service = PlotPublishingService(db)

        # Validate quality grade
        if request.quality_grade.upper() not in ["A", "B", "C"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Quality grade must be A, B, or C"
            )

        # Validate harvest date format
        try:
            harvest_date = date.fromisoformat(request.expected_harvest_date)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid harvest date format. Use YYYY-MM-DD",
            )

        # Publish plot to marketplace
        listing = await service.publish_plot(
            plot_id=plot_id,
            crop_name=request.crop_name,
            crop_variety=request.crop_variety,
            expected_harvest_date=request.expected_harvest_date,
            quantity_quintals=request.quantity_quintals,
            quality_grade=request.quality_grade.upper(),
            price_per_quintal=request.price_per_quintal,
            farmer_id=_user_id(current_user),
            user=current_user,
        )

        return listing

    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Plot publishing failed: {str(e)}",
        )


@router.get("/{plot_id}/listings", status_code=status.HTTP_200_OK)
async def get_plot_listings(
    plot_id: int, db: AsyncSession = Depends(get_db), current_user: dict = Depends(get_current_user)
):
    """
    Get all marketplace listings for a specific plot

    Returns all published listings for this plot, including:
    - Active listings
    - Completed listings
    - Cancelled listings

    Useful for farmers to track their plot's marketplace history.
    """
    # Owner check: someone else's plot is 404.
    try:
        plot = plot_for_user(plot_id, current_user)
    except LookupError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Plot {plot_id} not found"
        )
    try:
        # marketplace_listings has no plot_id column, so listings are matched on the plot's farm
        # (the old query compared farm_id with the plot id).
        listings = fetch_all(
            "SELECT * FROM marketplace_listings WHERE farm_id = ? ORDER BY created_at DESC, id DESC",
            [plot.farm_id],
        )

        # Format response
        response = []
        for listing in listings:
            response.append(
                {
                    "listing_id": listing.id,
                    "crop_type": listing.crop_type,
                    "crop_variety": listing.crop_variety,
                    "expected_harvest_date": (
                        listing.expected_harvest_date.isoformat()
                        if listing.expected_harvest_date
                        else None
                    ),
                    "estimated_quantity": listing.estimated_quantity,
                    "quality_grade": listing.quality_grade,
                    "status": listing.status,
                    "created_at": listing.created_at.isoformat() if listing.created_at else None,
                }
            )

        return {"plot_id": plot_id, "total_listings": len(response), "listings": response}

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get plot listings: {str(e)}",
        )
