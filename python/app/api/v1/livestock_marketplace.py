"""
Livestock Marketplace API Endpoints
Handles livestock marketplace listings, ROI calculations, and buyer-seller connections

CRUD goes through the generated services (app/core/crud_service.py); rows come back as dicts.
"""

from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from app.core.auth import get_current_active_user
from app.core.db import DB
from app.orm.user import User
from app.schemas.livestock_marketplace_listing import (
    LivestockMarketplaceListingCreate,
    LivestockMarketplaceListingList,
    LivestockMarketplaceListingResponse,
    LivestockMarketplaceListingUpdate,
)
from app.services.livestock_marketplace_listing_service import get_service as get_listing_service
from app.services.livestock_roi_service import get_roi_calculator
from app.services.livestock_service import get_service as get_livestock_service

router = APIRouter(prefix="/livestock-marketplace", tags=["livestock-marketplace"])
listings = get_listing_service()
livestock_rows = get_livestock_service()


def _listing(row: dict) -> dict:
    return dict(row, break_even_achieved=bool(row.get("break_even_achieved")))


def _own_listing(listing_id: int, current_user) -> dict:
    listing = listings.find(listing_id)
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")
    if (
        listing["farmer_id"] != current_user.id
        and getattr(current_user, "user_type", None) != "admin"
    ):
        raise HTTPException(status_code=403, detail="Not authorized to change this listing")
    return listing


class ROICalculationRequest(BaseModel):
    """Request model for ROI calculation"""

    species: str = Field(..., description="Animal species (cattle, buffalo, goat, poultry)")
    purpose: str = Field(..., description="Purpose (dairy, meat, breeding, eggs)")
    purchase_price: float = Field(..., gt=0, description="Initial purchase price")
    current_age_months: int = Field(..., gt=0, description="Current age in months")
    total_investment: float = Field(
        ..., gt=0, description="Total investment including feed, healthcare"
    )
    total_revenue: float = Field(default=0, ge=0, description="Total revenue generated so far")
    milk_production_liters_per_day: Optional[float] = Field(
        None, ge=0, description="Daily milk production (for dairy)"
    )


class ROICalculationResponse(BaseModel):
    """Response model for ROI calculation"""

    current_roi_percentage: float
    net_profit: float
    break_even_achieved: bool
    break_even_date: Optional[str]
    projected_annual_profit: float
    monthly_costs: float
    monthly_revenue: float
    monthly_cash_flow: float
    payback_period_months: Optional[int]
    investment_summary: dict
    recommendations: Optional[List[str]] = None


@router.post("/listings", response_model=LivestockMarketplaceListingResponse)
async def create_livestock_listing(
    listing_data: LivestockMarketplaceListingCreate,
    current_user: User = Depends(get_current_active_user),
):
    """
    Create a new livestock marketplace listing with automatic ROI calculation
    """
    livestock = livestock_rows.find(listing_data.livestock_id)
    if not livestock:
        raise HTTPException(status_code=404, detail="Livestock not found")
    if livestock["farmer_id"] != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to list this livestock")

    roi_metrics = get_roi_calculator().calculate_roi(
        species=livestock["species"],
        purpose=livestock["purpose"],
        purchase_price=float(livestock["purchase_price"]),
        current_age_months=listing_data.current_age_months,
        total_investment=float(listing_data.total_investment),
        total_revenue=float(listing_data.total_revenue),
        milk_production_liters_per_day=(
            float(listing_data.milk_production_liters_per_day)
            if listing_data.milk_production_liters_per_day
            else None
        ),
    )

    listing_dict = listing_data.model_dump()
    listing_dict.update(
        farmer_id=current_user.id,
        current_roi_percentage=roi_metrics["current_roi_percentage"],
        break_even_achieved=1 if roi_metrics["break_even_achieved"] else 0,
        break_even_date=roi_metrics["break_even_date"],
        projected_annual_profit=roi_metrics["projected_annual_profit"],
    )
    return _listing(listings.create(listing_dict))


@router.get("/listings", response_model=LivestockMarketplaceListingList)
async def get_livestock_listings(
    species: Optional[str] = Query(None, description="Filter by species"),
    listing_type: Optional[str] = Query(None, description="Filter by listing type"),
    state: Optional[str] = Query(None, description="Filter by state"),
    district: Optional[str] = Query(None, description="Filter by district"),
    min_price: Optional[float] = Query(None, description="Minimum asking price"),
    max_price: Optional[float] = Query(None, description="Maximum asking price"),
    min_roi: Optional[float] = Query(None, description="Minimum ROI percentage"),
    health_status: Optional[str] = Query(None, description="Filter by health status"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
):
    """
    Browse active livestock marketplace listings with filters (public)
    """
    where, bind = ["m.listing_status = 'active'"], []
    for column, value in (
        ("m.listing_type", listing_type),
        ("m.location_state", state),
        ("m.location_district", district),
        ("m.health_status", health_status),
    ):
        if value:
            where.append(f"{column} = ?")
            bind.append(value)
    if species:
        where.append("l.species ILIKE ?")
        bind.append(species)
    if min_price is not None:
        where.append("m.asking_price >= ?")
        bind.append(min_price)
    if max_price is not None:
        where.append("m.asking_price <= ?")
        bind.append(max_price)
    if min_roi is not None:
        where.append("m.current_roi_percentage >= ?")
        bind.append(min_roi)
    base = f"FROM livestock_marketplace_listings m JOIN livestock l ON l.id = m.livestock_id WHERE {' AND '.join(where)}"
    total = DB.raw(f"SELECT COUNT(*) AS n {base}", bind).result[0]["n"]
    rows = DB.raw(
        f"SELECT m.*, l.species, l.breed {base} ORDER BY m.id DESC LIMIT ? OFFSET ?",
        bind + [page_size, (page - 1) * page_size],
    ).result
    return {
        "listings": [_listing(r) for r in rows],
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": (total + page_size - 1) // page_size,
    }


@router.get("/listings/{listing_id}", response_model=LivestockMarketplaceListingResponse)
async def get_livestock_listing_detail(listing_id: int):
    """
    Get detailed information about a livestock listing (public; counts a view)
    """
    listing = listings.find(listing_id)
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")
    DB.raw(
        "UPDATE livestock_marketplace_listings SET views_count = COALESCE(views_count, 0) + 1 WHERE id = ?",
        [listing_id],
    )
    return _listing(dict(listing, views_count=(listing.get("views_count") or 0) + 1))


@router.post("/calculate-roi", response_model=ROICalculationResponse)
async def calculate_livestock_roi(
    request: ROICalculationRequest, current_user: User = Depends(get_current_active_user)
):
    """
    Calculate ROI for livestock investment (standalone calculator)
    """
    roi_calculator = get_roi_calculator()

    roi_metrics = roi_calculator.calculate_roi(
        species=request.species,
        purpose=request.purpose,
        purchase_price=request.purchase_price,
        current_age_months=request.current_age_months,
        total_investment=request.total_investment,
        total_revenue=request.total_revenue,
        milk_production_liters_per_day=request.milk_production_liters_per_day,
    )

    # Generate recommendations
    livestock_data = {
        "species": request.species,
        "purpose": request.purpose,
        "current_age_months": request.current_age_months,
    }
    recommendations = roi_calculator._generate_recommendations(roi_metrics, livestock_data)
    roi_metrics["recommendations"] = recommendations

    return roi_metrics


@router.get("/listings/{listing_id}/roi-report")
async def get_livestock_roi_report(listing_id: int):
    """
    Get comprehensive ROI report for a livestock listing
    """
    listing = listings.find(listing_id)
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")
    livestock = livestock_rows.find(listing["livestock_id"])
    if not livestock:
        raise HTTPException(status_code=404, detail="Livestock not found")

    roi_calculator = get_roi_calculator()
    roi_metrics = roi_calculator.calculate_roi(
        species=livestock["species"],
        purpose=livestock["purpose"],
        purchase_price=float(livestock["purchase_price"]),
        current_age_months=listing["current_age_months"],
        total_investment=float(listing["total_investment"]),
        total_revenue=float(listing["total_revenue"] or 0),
        milk_production_liters_per_day=(
            float(listing["milk_production_liters_per_day"])
            if listing.get("milk_production_liters_per_day")
            else None
        ),
    )
    livestock_data = {
        "species": livestock["species"],
        "breed": livestock["breed"],
        "purpose": livestock["purpose"],
        "current_age_months": listing["current_age_months"],
    }
    return roi_calculator.generate_roi_report(livestock_data, roi_metrics)


@router.put("/listings/{listing_id}", response_model=LivestockMarketplaceListingResponse)
async def update_livestock_listing(
    listing_id: int,
    listing_data: LivestockMarketplaceListingUpdate,
    current_user: User = Depends(get_current_active_user),
):
    """
    Update a livestock marketplace listing (owner or admin)
    """
    _own_listing(listing_id, current_user)
    data = listing_data.model_dump(exclude_unset=True)
    data.pop("farmer_id", None)
    return _listing(listings.update(listing_id, data))


@router.delete("/listings/{listing_id}")
async def delete_livestock_listing(
    listing_id: int, current_user: User = Depends(get_current_active_user)
):
    """
    Delete a livestock marketplace listing (owner or admin)
    """
    _own_listing(listing_id, current_user)
    listings.delete(listing_id)
    return {"message": "Listing deleted successfully"}
