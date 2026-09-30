"""
Transport coordination API endpoints for livestock marketplace.
"""

from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field

from app.core.auth import get_current_active_user
from app.services.transport_service import transport_service

router = APIRouter(
    prefix="/transport", tags=["transport"], dependencies=[Depends(get_current_active_user)]
)
# Request/Response Models


class TransportProviderCreate(BaseModel):
    """Request model for registering a transport provider."""

    user_id: Optional[int] = Field(
        None, description="Ignored; the provider belongs to the signed-in user"
    )
    company_name: str = Field(..., min_length=1, max_length=255)
    contact_person: str = Field(..., min_length=1, max_length=255)
    contact_phone: str = Field(..., min_length=10, max_length=20)
    contact_email: Optional[str] = None
    service_areas: List[str] = Field(..., min_items=1, description="States/districts served")
    vehicle_types: List[str] = Field(
        ..., min_items=1, description="truck, tempo, mini_truck, specialized_livestock"
    )
    livestock_specialization: Optional[List[str]] = Field(
        None, description="cattle, goat, sheep, poultry, buffalo"
    )
    base_rate_per_km: float = Field(..., gt=0, description="Base rate in INR per kilometer")
    minimum_charge: float = Field(..., gt=0, description="Minimum charge in INR")
    max_capacity_animals: int = Field(..., gt=0, description="Maximum animals per trip")
    insurance_available: bool = False
    insurance_rate_percentage: Optional[float] = Field(None, ge=0, le=100)
    license_number: Optional[str] = None
    verification_documents: Optional[List[str]] = None


class TransportProviderUpdate(BaseModel):
    """Request model for updating transport provider."""

    company_name: Optional[str] = None
    contact_person: Optional[str] = None
    contact_phone: Optional[str] = None
    contact_email: Optional[str] = None
    service_areas: Optional[List[str]] = None
    vehicle_types: Optional[List[str]] = None
    livestock_specialization: Optional[List[str]] = None
    base_rate_per_km: Optional[float] = Field(None, gt=0)
    minimum_charge: Optional[float] = Field(None, gt=0)
    max_capacity_animals: Optional[int] = Field(None, gt=0)
    insurance_available: Optional[bool] = None
    insurance_rate_percentage: Optional[float] = Field(None, ge=0, le=100)
    license_number: Optional[str] = None
    verification_documents: Optional[List[str]] = None
    status: Optional[str] = Field(None, pattern="^(active|inactive|suspended)$")


class TransportProviderResponse(BaseModel):
    """Response model for transport provider."""

    id: int
    user_id: int
    company_name: str
    contact_person: str
    contact_phone: str
    contact_email: Optional[str]
    service_areas: str  # JSON string
    vehicle_types: str  # JSON string
    livestock_specialization: Optional[str]  # JSON string
    base_rate_per_km: float
    minimum_charge: float
    insurance_available: bool
    insurance_rate_percentage: Optional[float]
    max_capacity_animals: int
    rating: float
    total_ratings: int
    completed_transports: int
    verified: bool
    license_number: Optional[str]
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


class CostEstimateRequest(BaseModel):
    """Request model for transport cost estimate."""

    provider_id: int
    pickup_latitude: Optional[float] = None
    pickup_longitude: Optional[float] = None
    delivery_latitude: Optional[float] = None
    delivery_longitude: Optional[float] = None
    livestock_type: str = Field(..., pattern="^(cattle|goat|sheep|poultry|buffalo)$")
    livestock_count: int = Field(..., gt=0)
    animal_value: float = Field(..., gt=0)
    insurance_opted: bool = False


class CostEstimateResponse(BaseModel):
    """Response model for transport cost estimate."""

    distance_km: float
    transport_cost: float
    insurance_cost: float
    total_cost: float
    provider_name: str
    estimated_travel_hours: float


class TransportBookingCreate(BaseModel):
    """Request model for creating transport booking."""

    transaction_id: int
    provider_id: int
    requester_id: Optional[int] = Field(
        None, description="Ignored; the requester is the signed-in user"
    )
    pickup_address: str = Field(..., min_length=10)
    pickup_latitude: Optional[float] = None
    pickup_longitude: Optional[float] = None
    delivery_address: str = Field(..., min_length=10)
    delivery_latitude: Optional[float] = None
    delivery_longitude: Optional[float] = None
    livestock_type: str = Field(..., pattern="^(cattle|goat|sheep|poultry|buffalo)$")
    livestock_count: int = Field(..., gt=0)
    animal_value: float = Field(..., gt=0)
    scheduled_pickup_date: datetime
    insurance_opted: bool = False
    special_instructions: Optional[str] = None


class TransportBookingResponse(BaseModel):
    """Response model for transport booking."""

    id: int
    transaction_id: int
    provider_id: int
    requester_id: int
    pickup_address: str
    pickup_latitude: Optional[float]
    pickup_longitude: Optional[float]
    delivery_address: str
    delivery_latitude: Optional[float]
    delivery_longitude: Optional[float]
    distance_km: float
    livestock_type: str
    livestock_count: int
    animal_value: float
    transport_cost: float
    insurance_opted: bool
    insurance_cost: Optional[float]
    total_cost: float
    scheduled_pickup_date: datetime
    estimated_delivery_date: datetime
    actual_pickup_date: Optional[datetime]
    actual_delivery_date: Optional[datetime]
    status: str
    tracking_updates: Optional[str]  # JSON string
    special_instructions: Optional[str]
    rating: Optional[int]
    review: Optional[str]
    reviewed_at: Optional[datetime]
    created_at: datetime
    cancelled_at: Optional[datetime] = None
    cancellation_reason: Optional[str] = None
    provider_name: Optional[str] = None

    class Config:
        from_attributes = True


class StatusUpdate(BaseModel):
    """Request model for updating booking status."""

    status: str = Field(..., pattern="^(pending|confirmed|in_transit|delivered|cancelled)$")
    message: Optional[str] = None
    actual_pickup_date: Optional[datetime] = None
    actual_delivery_date: Optional[datetime] = None


class RatingReview(BaseModel):
    """Request model for adding rating and review."""

    rating: int = Field(..., ge=1, le=5)
    review: Optional[str] = None


class CancellationRequest(BaseModel):
    """Request model for cancelling booking."""

    cancellation_reason: str = Field(..., min_length=10)


def _run(fn, *args, **kwargs):
    """Map service errors to HTTP status codes."""
    try:
        return fn(*args, **kwargs)
    except LookupError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


# Transport Provider Endpoints


@router.post(
    "/providers", response_model=TransportProviderResponse, status_code=status.HTTP_201_CREATED
)
async def register_provider(
    provider_data: TransportProviderCreate,
    current_user=Depends(get_current_active_user),
):
    """Register a transport provider owned by the signed-in user (any client-sent user_id is ignored)."""
    data = provider_data.model_dump(exclude={"user_id"})
    return _run(transport_service.register_provider, current_user, **data)


@router.get("/providers/{provider_id}", response_model=TransportProviderResponse)
async def get_provider(provider_id: int):
    """Get transport provider details."""
    return _run(transport_service.get_provider, provider_id)


@router.get("/providers", response_model=List[TransportProviderResponse])
async def search_providers(
    state: Optional[str] = None,
    district: Optional[str] = None,
    livestock_type: Optional[str] = None,
    min_capacity: Optional[int] = None,
    insurance_required: bool = False,
    verified_only: bool = False,
    mine: bool = Query(False, description="Only providers registered by the signed-in user"),
    current_user=Depends(get_current_active_user),
):
    """Search for active transport providers."""
    return _run(
        transport_service.search_providers,
        state=state,
        district=district,
        livestock_type=livestock_type,
        min_capacity=min_capacity,
        insurance_required=insurance_required,
        verified_only=verified_only,
        user_id=current_user.id if mine else None,
    )


@router.put("/providers/{provider_id}", response_model=TransportProviderResponse)
async def update_provider(
    provider_id: int,
    updates: TransportProviderUpdate,
    current_user=Depends(get_current_active_user),
):
    """Update transport provider details (owner or admin only)."""
    update_data = {k: v for k, v in updates.model_dump().items() if v is not None}
    return _run(transport_service.update_provider, provider_id, current_user, **update_data)


# Cost Estimation Endpoint


@router.post("/cost-estimate", response_model=CostEstimateResponse)
async def estimate_transport_cost(estimate_request: CostEstimateRequest):
    """Calculate transport cost estimate."""
    r = estimate_request
    return _run(
        transport_service.estimate,
        r.provider_id,
        r.pickup_latitude,
        r.pickup_longitude,
        r.delivery_latitude,
        r.delivery_longitude,
        r.livestock_type,
        r.livestock_count,
        r.animal_value,
        r.insurance_opted,
    )


# Transport Booking Endpoints


@router.post(
    "/bookings", response_model=TransportBookingResponse, status_code=status.HTTP_201_CREATED
)
async def create_booking(
    booking_data: TransportBookingCreate,
    current_user=Depends(get_current_active_user),
):
    """Create a transport booking for a livestock transaction the signed-in user is buyer or seller of."""
    data = booking_data.model_dump(exclude={"requester_id"})
    return _run(transport_service.create_booking, current_user, **data)


@router.get("/bookings", response_model=List[TransportBookingResponse])
async def list_bookings(
    status_filter: Optional[str] = Query(None, alias="status"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    current_user=Depends(get_current_active_user),
):
    """Transport bookings the signed-in user is involved in (requester, provider, buyer or seller)."""
    return _run(transport_service.list_bookings, current_user, status_filter, skip, limit)


def _booking_for(booking_id: int, current_user):
    return _run(transport_service.get_booking, booking_id, current_user)


@router.get("/tracking/{booking_id}", response_model=TransportBookingResponse)
async def track_booking_by_id_alias(booking_id: int, current_user=Depends(get_current_active_user)):
    """Registry alias for tracking booking by booking_id"""
    return _booking_for(booking_id, current_user)


# Same path as the route above, so it never matches; kept (hidden from the docs) for compatibility.
@router.get("/tracking/{id}", response_model=TransportBookingResponse, include_in_schema=False)
async def track_booking_alias(id: int, current_user=Depends(get_current_active_user)):
    """Registry alias for tracking booking"""
    return _booking_for(id, current_user)


# Static /bookings/<word>/... routes are registered before /bookings/{id}.
@router.get("/bookings/transaction/{transaction_id}", response_model=List[TransportBookingResponse])
async def get_transaction_bookings(
    transaction_id: int, current_user=Depends(get_current_active_user)
):
    """Get all transport bookings for a livestock transaction (buyer, seller or admin)."""
    return _run(transport_service.get_bookings_for_transaction, transaction_id, current_user)


@router.get("/bookings/provider/{provider_id}", response_model=List[TransportBookingResponse])
async def get_provider_bookings(
    provider_id: int,
    status_filter: Optional[str] = Query(None, alias="status"),
    current_user=Depends(get_current_active_user),
):
    """Get all bookings for a provider (provider's owner or admin)."""
    return _run(transport_service.get_provider_bookings, provider_id, current_user, status_filter)


@router.get("/bookings/{id}", response_model=TransportBookingResponse)
async def get_booking(id: int, current_user=Depends(get_current_active_user)):
    """Get transport booking details (parties to the booking or admin)."""
    return _booking_for(id, current_user)


@router.put("/bookings/{booking_id}/status", response_model=TransportBookingResponse)
async def update_booking_status(
    booking_id: int,
    status_update: StatusUpdate,
    current_user=Depends(get_current_active_user),
):
    """Update transport booking status (provider or admin; 'cancelled' is open to any party)."""
    return _run(
        transport_service.update_booking_status,
        booking_id,
        current_user,
        status_update.status,
        status_update.message,
        status_update.actual_pickup_date,
        status_update.actual_delivery_date,
    )


@router.post("/bookings/{booking_id}/review", response_model=TransportBookingResponse)
async def add_rating_review(
    booking_id: int,
    rating_review: RatingReview,
    current_user=Depends(get_current_active_user),
):
    """Add rating and review for a delivered transport (customer side only, once)."""
    return _run(
        transport_service.add_rating_and_review,
        booking_id,
        current_user,
        rating_review.rating,
        rating_review.review,
    )


@router.post("/bookings/{booking_id}/cancel", response_model=TransportBookingResponse)
async def cancel_booking(
    booking_id: int,
    cancellation: CancellationRequest,
    current_user=Depends(get_current_active_user),
):
    """Cancel an open transport booking (any party or admin)."""
    return _run(
        transport_service.cancel_booking, booking_id, current_user, cancellation.cancellation_reason
    )
