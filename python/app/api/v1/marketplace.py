"""
Marketplace API endpoints
"""

import logging
import uuid
from datetime import date, datetime, timedelta
from typing import Annotated, Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import DB, CurrentFarmer, CurrentUser, MarketplaceSvc
from app.orm.buyer_interest import BuyerInterest
from app.orm.marketplace_listing import MarketplaceListing
from app.orm.user import User
from app.services.marketplace_service import MarketplaceService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/marketplace")


# Request/Response Schemas
class CreateListingRequest(BaseModel):
    """Request to create marketplace listing"""

    crop_id: str = Field(..., description="Crop ID")
    yield_prediction: Optional[Dict[str, Any]] = Field(
        None, description="Optional yield prediction data"
    )


class BuyerInterestRequest(BaseModel):
    """Request to register buyer interest"""

    listing_id: str
    interest_type: str = Field(default="inquiry", description="inquiry, booking_intent, firm_order")
    quantity_interested: Optional[float] = None
    preferred_price: Optional[float] = None
    buyer_phone: Optional[str] = None
    buyer_email: Optional[str] = None
    buyer_company: Optional[str] = None
    quality_requirements: Optional[str] = None
    delivery_requirements: Optional[str] = None
    payment_terms: Optional[str] = None
    message: Optional[str] = None


class ListingResponse(BaseModel):
    """Listing response"""

    id: str
    title: str
    description: str
    crop_type: str
    crop_variety: str
    estimated_quantity: float
    quality_grade: str
    expected_harvest_date: str
    harvest_window_start: str
    harvest_window_end: str
    asking_price_per_unit: float
    location_state: str
    location_district: str
    farmer_phone: Optional[str]
    farmer_email: Optional[str]
    status: str
    view_count: int
    interest_count: int
    listed_at: str


@router.post("/listings", response_model=Dict[str, Any])
async def create_listing(
    request: CreateListingRequest,
    current_user: CurrentFarmer,
    db: DB,
    marketplace_service: MarketplaceSvc,
):
    """
    Create automatic marketplace listing for a crop

    Validates: AC4.1 - Automatic listing when farmer confirms crop selection
    Validates: AC4.2 - Include all required fields
    """
    try:
        if not str(request.crop_id).isdigit():
            raise ValueError("Crop not found")
        listing = marketplace_service.create_automatic_listing(
            crop_id=int(request.crop_id),
            farmer_id=current_user.id,
            yield_prediction=request.yield_prediction,
        )
        harvest = listing["expected_harvest_date"]
        return {
            "success": True,
            "listing_id": str(listing["id"]),
            "message": "Marketplace listing created successfully",
            "listing": {
                "id": str(listing["id"]),
                "title": listing["crop_type"],
                "crop_type": listing["crop_type"],
                "estimated_quantity": float(listing["estimated_quantity"]),
                "expected_harvest_date": (
                    harvest.isoformat() if hasattr(harvest, "isoformat") else harvest
                ),
                "status": listing["status"],
            },
        }

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating listing: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create listing: {str(e)}",
        )


@router.get("/search", response_model=Dict[str, Any])
async def search_listings_alias(
    db: DB,
    marketplace_service: MarketplaceSvc,
    crop_type: Optional[str] = Query(None),
    state: Optional[str] = Query(None),
    district: Optional[str] = Query(None),
):
    """Registry alias for marketplace search"""
    # Pass every parameter: calling the route function directly would leave its Query() defaults in place.
    return await get_listings(
        db,
        marketplace_service,
        crop_type=crop_type,
        state=state,
        district=district,
        min_quantity=None,
        max_quantity=None,
        harvest_from=None,
        harvest_to=None,
        quality_grade=None,
        min_price=None,
        max_price=None,
        sort_by="harvest_date",
        sort_order="asc",
        page=1,
        page_size=20,
    )


@router.get("/listings", response_model=Dict[str, Any])
async def get_listings(
    db: DB,
    marketplace_service: MarketplaceSvc,
    crop_type: Optional[str] = Query(None, description="Filter by crop type (partial match)"),
    state: Optional[str] = Query(None, description="Filter by state"),
    district: Optional[str] = Query(None, description="Filter by district"),
    min_quantity: Optional[float] = Query(None, description="Minimum quantity in quintals"),
    max_quantity: Optional[float] = Query(None, description="Maximum quantity in quintals"),
    harvest_from: Optional[date] = Query(None, description="Harvest date from (YYYY-MM-DD)"),
    harvest_to: Optional[date] = Query(None, description="Harvest date to (YYYY-MM-DD)"),
    quality_grade: Optional[str] = Query(None, description="Quality grade (A, B, C)"),
    min_price: Optional[float] = Query(None, description="Minimum price per unit"),
    max_price: Optional[float] = Query(None, description="Maximum price per unit"),
    sort_by: str = Query(
        "harvest_date", description="Sort by: harvest_date, quantity, quality_grade, price"
    ),
    sort_order: str = Query("asc", description="Sort order: asc, desc"),
    page: int = Query(1, ge=1, description="Page number (starts at 1)"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page (max 100)"),
):
    """
    Get marketplace listings with filters, sorting, and pagination

    Validates: AC4 - Marketplace search functionality

    **Filters:**
    - crop_type: Filter by crop type (partial match, case-insensitive)
    - state: Filter by state (exact match)
    - district: Filter by district (exact match)
    - min_quantity/max_quantity: Filter by quantity range
    - harvest_from/harvest_to: Filter by harvest date range
    - quality_grade: Filter by quality grade (A, B, C)
    - min_price/max_price: Filter by price range

    **Sorting:**
    - sort_by: harvest_date (default), quantity, quality_grade, price
    - sort_order: asc (default), desc

    **Pagination:**
    - page: Page number (starts at 1)
    - page_size: Items per page (default 20, max 100)

    **Returns:**
    - listings: Array of listing objects
    - pagination: Pagination metadata (page, page_size, total_items, total_pages)
    """
    try:
        # Build filters dictionary
        filters = {}
        if crop_type:
            filters["crop_type"] = crop_type
        if state:
            filters["state"] = state
        if district:
            filters["district"] = district
        if min_quantity is not None:
            filters["min_quantity"] = min_quantity
        if max_quantity is not None:
            filters["max_quantity"] = max_quantity
        if harvest_from:
            filters["harvest_from"] = harvest_from
        if harvest_to:
            filters["harvest_to"] = harvest_to
        if quality_grade:
            filters["quality_grade"] = quality_grade.upper()
        if min_price is not None:
            filters["min_price"] = min_price
        if max_price is not None:
            filters["max_price"] = max_price

        # Calculate offset from page number
        offset = (page - 1) * page_size

        # Get listings with total count
        listings, total_count = marketplace_service.get_listings(
            filters=filters, sort_by=sort_by, sort_order=sort_order, limit=page_size, offset=offset
        )

        # Calculate pagination metadata
        total_pages = (total_count + page_size - 1) // page_size  # Ceiling division

        # Build response
        result = []
        for listing in listings:
            # listing is now a dict from custom ORM, not an ORM object
            result.append(
                {
                    "id": str(listing["id"]),
                    "title": listing.get("title"),
                    "description": listing.get("description"),
                    "crop_type": listing.get("crop_type"),
                    "crop_variety": listing.get("crop_variety"),
                    "estimated_quantity": (
                        float(listing["estimated_quantity"])
                        if listing.get("estimated_quantity")
                        else None
                    ),
                    "quantity_unit": listing.get("quantity_unit"),
                    "quality_grade": listing.get("quality_grade"),
                    "quality_confidence": (
                        float(listing["quality_confidence"])
                        if listing.get("quality_confidence")
                        else None
                    ),
                    "expected_harvest_date": (
                        listing["expected_harvest_date"].isoformat()
                        if listing.get("expected_harvest_date")
                        else None
                    ),
                    "harvest_window": {
                        "start": (
                            listing["harvest_window_start"].isoformat()
                            if listing.get("harvest_window_start")
                            else None
                        ),
                        "end": (
                            listing["harvest_window_end"].isoformat()
                            if listing.get("harvest_window_end")
                            else None
                        ),
                    },
                    "asking_price_per_unit": (
                        float(listing["asking_price_per_unit"])
                        if listing.get("asking_price_per_unit")
                        else None
                    ),
                    "price_negotiable": listing.get("price_negotiable"),
                    "location": {
                        "state": listing.get("location_state"),
                        "district": listing.get("location_district"),
                        "block": listing.get("location_block"),
                    },
                    "contact": {
                        "enabled": listing.get("contact_enabled"),
                        "phone": (
                            listing.get("farmer_phone") if listing.get("contact_enabled") else None
                        ),
                        "email": (
                            listing.get("farmer_email") if listing.get("contact_enabled") else None
                        ),
                    },
                    "market_intelligence": {
                        "demand_score": (
                            float(listing["market_demand_score"])
                            if listing.get("market_demand_score")
                            else None
                        ),
                        "price_trend": listing.get("price_trend"),
                        "yoy_growth": (
                            float(listing["yoy_price_growth"])
                            if listing.get("yoy_price_growth")
                            else None
                        ),
                    },
                    "status": listing.get("status"),
                    "view_count": listing.get("view_count"),
                    "interest_count": listing.get("interest_count"),
                    "listed_at": (
                        listing["listed_at"].isoformat() if listing.get("listed_at") else None
                    ),
                }
            )

        return {
            "success": True,
            "listings": result,
            "pagination": {
                "page": page,
                "page_size": page_size,
                "total_items": total_count,
                "total_pages": total_pages,
                "has_next": page < total_pages,
                "has_prev": page > 1,
            },
            "filters_applied": filters,
            "sort": {"by": sort_by, "order": sort_order},
        }

    except Exception as e:
        logger.error(f"Error getting listings: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get listings: {str(e)}",
        )


@router.post("/buyer-interest")
async def register_buyer_interest(
    request: BuyerInterestRequest,
    current_user: CurrentUser,
    db: DB,
    marketplace_service: MarketplaceSvc,
):
    """
    Register buyer interest in a listing

    Validates: AC4.3 - Buyers can express interest in advance booking
    """
    try:
        interest_data = {
            "interest_type": request.interest_type,
            "quantity_interested": request.quantity_interested,
            "preferred_price": request.preferred_price,
            "buyer_phone": request.buyer_phone,
            "buyer_email": request.buyer_email,
            "buyer_company": request.buyer_company,
            "quality_requirements": request.quality_requirements,
            "delivery_requirements": request.delivery_requirements,
            "payment_terms": request.payment_terms,
            "message": request.message,
        }

        interest = marketplace_service.register_buyer_interest(
            listing_id=int(request.listing_id),
            buyer_id=current_user.id,
            interest_data=interest_data,
        )

        return {
            "success": True,
            "interest_id": str(interest["id"]),
            "message": "Buyer interest registered successfully",
            "status": interest["status"],
        }

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Error registering buyer interest: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to register interest: {str(e)}",
        )


@router.get("/listings/buyer-dashboard", response_model=Dict[str, Any])
async def get_buyer_dashboard_overview(
    current_user: CurrentUser,
    db: DB,
):
    """Provide overview data for the buyer interests dashboard"""

    def _to_datetime(value: Any) -> Optional[datetime]:
        if isinstance(value, datetime):
            return value
        if isinstance(value, str):
            try:
                # Support timestamps with or without timezone suffix
                return datetime.fromisoformat(value.replace("Z", "+00:00"))
            except ValueError:
                return None
        return None

    try:
        listings_result = MarketplaceListing.where({"farmer_id": [current_user.id]}).get()
        listings = (
            listings_result.items if listings_result and hasattr(listings_result, "items") else []
        )
        listing_ids = [listing["id"] for listing in listings if listing.get("id")]

        interests: List[Dict[str, Any]] = []
        if listing_ids:
            interests_result = BuyerInterest.where({"listing_id": listing_ids}).get()
            interests = (
                interests_result.items
                if interests_result and hasattr(interests_result, "items")
                else []
            )

        # Build lookup of interest counts per listing
        interest_counts: Dict[str, int] = {}
        last_interest_at: Optional[datetime] = None
        last_7_days = datetime.utcnow() - timedelta(days=7)
        interests_last_week = 0
        pending_followups = 0

        for interest in interests:
            listing_key = str(interest.get("listing_id"))
            interest_counts[listing_key] = interest_counts.get(listing_key, 0) + 1

            created_at = _to_datetime(interest.get("created_at"))
            if created_at:
                if created_at > last_7_days:
                    interests_last_week += 1
                if (not last_interest_at) or created_at > last_interest_at:
                    last_interest_at = created_at

            if (interest.get("status") or "").lower() in {"pending", "new"}:
                pending_followups += 1

        top_listings = []
        for listing in listings:
            listing_id = str(listing.get("id"))
            top_listings.append(
                {
                    "id": listing_id,
                    "title": listing.get("title") or listing.get("crop_type"),
                    "crop_type": listing.get("crop_type"),
                    "interest_count": interest_counts.get(
                        listing_id, listing.get("interest_count", 0) or 0
                    ),
                    "status": listing.get("status"),
                    "expected_harvest_date": (
                        listing.get("expected_harvest_date").isoformat()
                        if hasattr(listing.get("expected_harvest_date"), "isoformat")
                        else listing.get("expected_harvest_date")
                    ),
                }
            )

        top_listings.sort(key=lambda item: item["interest_count"], reverse=True)
        top_listings = top_listings[:5]

        recent_interests = []
        for interest in interests:
            created_at = _to_datetime(interest.get("created_at"))
            recent_interests.append(
                {
                    "id": str(interest.get("id")),
                    "listing_id": str(interest.get("listing_id")),
                    "buyer_name": interest.get("buyer_name"),
                    "buyer_company": interest.get("buyer_company"),
                    "quantity": interest.get("interested_quantity")
                    or interest.get("quantity_interested"),
                    "status": interest.get("status"),
                    "created_at": (
                        created_at.isoformat() if created_at else interest.get("created_at")
                    ),
                }
            )

        recent_interests.sort(key=lambda item: item.get("created_at") or "", reverse=True)
        recent_interests = recent_interests[:10]

        summary = {
            "listings_tracked": len(listings),
            "total_interests": len(interests),
            "interests_last_7_days": interests_last_week,
            "pending_followups": pending_followups,
            "last_interest_at": last_interest_at.isoformat() if last_interest_at else None,
        }

        return {
            "success": True,
            "summary": summary,
            "top_listings": top_listings,
            "recent_interests": recent_interests,
        }
    except Exception as e:
        logger.error(f"Error building buyer dashboard overview: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get buyer dashboard data: {str(e)}",
        )


@router.get("/my-listings", response_model=Dict[str, Any])
async def get_my_listings(
    current_user: CurrentUser,
    db: DB,
    status_filter: Optional[str] = Query(
        None, description="Filter by status: active, sold, expired"
    ),
    page: int = Query(1, ge=1, description="Page number (starts at 1)"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page (max 100)"),
):
    """
    Get all marketplace listings for the current authenticated farmer

    Returns list of listings created by the farmer with:
    - Listing details (crop, quantity, price)
    - Status and view/interest counts
    - Harvest information
    - Location details

    Supports filtering by status and pagination.

    Validates: Dashboard functionality
    """
    try:
        # Use the custom ORM pattern instead of SQLAlchemy
        query = {"farmer_id": [current_user.id]}

        # Apply status filter if provided
        if status_filter:
            query["status"] = [status_filter]

        # Get listings
        listings_result = MarketplaceListing.where(query).get()
        all_listings = (
            listings_result.items if listings_result and hasattr(listings_result, "items") else []
        )

        # Get total count
        total_count = len(all_listings)

        # Sort and paginate
        all_listings.sort(key=lambda x: x.get("listed_at", ""), reverse=True)

        offset = (page - 1) * page_size
        paginated_listings = all_listings[offset : offset + page_size]

        # Calculate pagination metadata
        total_pages = (total_count + page_size - 1) // page_size if page_size > 0 else 0

        # Build response
        result = []
        for listing in paginated_listings:
            result.append(
                {
                    "id": str(listing["id"]),
                    "title": listing.get("title"),
                    "description": listing.get("description"),
                    "crop_type": listing.get("crop_type"),
                    "crop_variety": listing.get("crop_variety"),
                    "estimated_quantity": (
                        float(listing["estimated_quantity"])
                        if listing.get("estimated_quantity")
                        else None
                    ),
                    "quantity_unit": listing.get("quantity_unit"),
                    "quality_grade": listing.get("quality_grade"),
                    "expected_harvest_date": (
                        listing["expected_harvest_date"].isoformat()
                        if hasattr(listing.get("expected_harvest_date"), "isoformat")
                        else listing.get("expected_harvest_date")
                    ),
                    "asking_price_per_unit": (
                        float(listing["asking_price_per_unit"])
                        if listing.get("asking_price_per_unit")
                        else None
                    ),
                    "price_negotiable": listing.get("price_negotiable"),
                    "location": {
                        "state": listing.get("location_state"),
                        "district": listing.get("location_district"),
                    },
                    "status": listing.get("status"),
                    "view_count": listing.get("view_count", 0),
                    "interest_count": listing.get("interest_count", 0),
                    "listed_at": (
                        listing["listed_at"].isoformat()
                        if hasattr(listing.get("listed_at"), "isoformat")
                        else listing.get("listed_at")
                    ),
                }
            )

        logger.info(f"Retrieved {len(result)} listings for user {current_user.id}")

        return {
            "success": True,
            "listings": result,
            "pagination": {
                "page": page,
                "page_size": page_size,
                "total_items": total_count,
                "total_pages": total_pages,
                "has_next": page < total_pages,
                "has_prev": page > 1,
            },
        }

    except Exception as e:
        logger.error(f"Error getting my listings: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get listings: {str(e)}",
        )


@router.get("/listings/{id}")
async def get_listing_detail(id: str, db: DB, marketplace_service: MarketplaceSvc):
    """
    Get detailed listing information including production predictions and market intelligence

    Validates: AC4 - Listing detail view with full information

    Returns:
    - Full listing details
    - Production predictions (yield, harvest timing, quality)
    - Market intelligence context (YoY growth, demand trends, price trends)
    - Farmer contact options
    - Interest registration link
    """
    try:
        # Get listing with full details
        if not id.isdigit():
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Listing not found")
        listing_detail = marketplace_service.get_listing_detail(int(id))

        if not listing_detail:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Listing not found")

        return {"success": True, "listing": listing_detail}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting listing detail: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get listing detail: {str(e)}",
        )
