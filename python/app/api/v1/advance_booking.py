"""
Advance Booking API endpoints for pre-harvest booking system
Implements Task 27.2: Build advance booking system

Business rules live in app/services/booking_workflow.py. Every endpoint acts as the signed-in user:
only the buyer and farmer on a booking (or an admin) can see or change it.
"""

from datetime import date
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field, model_validator

from app.core.dependencies import CurrentUser
from app.services.booking_workflow import booking_workflow

router = APIRouter(prefix="/advance-bookings", tags=["Advance Booking"])


# Request/Response Schemas
class QualityStandards(BaseModel):
    """Quality standards specification"""

    grade: str = Field(..., description="Quality grade (A/B/C)")
    size: Optional[str] = Field(None, description="Size requirements")
    moisture_content: Optional[float] = Field(None, description="Maximum moisture content %")
    organic_certified: bool = Field(default=False, description="Organic certification required")
    defects_tolerance: Optional[float] = Field(None, description="Maximum defects tolerance %")
    additional_specs: Optional[Dict[str, Any]] = None


class ContractTerms(BaseModel):
    """Contract terms and conditions"""

    delivery_terms: str = Field(..., description="Delivery terms (FOB, CIF, etc.)")
    penalty_late_delivery: Optional[float] = Field(None, description="Penalty for late delivery")
    penalty_quality_failure: Optional[float] = Field(
        None, description="Penalty for quality failure"
    )
    cancellation_terms: Optional[str] = Field(None, description="Cancellation policy")
    dispute_resolution: Optional[str] = None
    additional_terms: Optional[str] = None


class CreateAdvanceBookingRequest(BaseModel):
    """Request to create advance booking (the buyer is always the signed-in user)"""

    listing_id: int = Field(..., description="Marketplace listing ID")
    quantity_booked: float = Field(..., description="Quantity to book (kg)", gt=0)
    price_per_unit: float = Field(..., description="Price per unit", gt=0)
    advance_payment_percent: int = Field(
        default=20, ge=20, le=50, description="Advance payment % (20-50%)"
    )
    expected_delivery_date: date = Field(..., description="Expected delivery date")
    quality_standards: QualityStandards = Field(..., description="Quality requirements")
    contract_terms: ContractTerms = Field(..., description="Contract terms")

    @model_validator(mode="before")
    @classmethod
    def accept_legacy_names(cls, data: Any) -> Any:
        # Older clients sent quantity / quality_requirement (and a buyer_id, which is ignored).
        if isinstance(data, dict):
            data = dict(data)
            if "quantity_booked" not in data and "quantity" in data:
                data["quantity_booked"] = data["quantity"]
            if "quality_standards" not in data and "quality_requirement" in data:
                data["quality_standards"] = data["quality_requirement"]
        return data


class StatusUpdateRequest(BaseModel):
    status: str = Field(..., description="confirmed | cancelled | completed")
    notes: Optional[str] = None


class QualityVerificationRequest(BaseModel):
    verifier_type: str = Field("buyer", description="platform | third_party | buyer")
    quality_grade: str
    quality_metrics: Dict[str, Any] = Field(default_factory=dict)
    photos: List[str] = Field(default_factory=list)
    passed: bool = True
    notes: Optional[str] = None


class DisputeRequest(BaseModel):
    dispute_reason: str = Field(..., min_length=3)
    details: Optional[str] = None
    photos: List[str] = Field(default_factory=list)


class PaymentRequest(BaseModel):
    milestone_type: str = Field(..., description="advance | quality_check | delivery | final")
    payment_method: Optional[str] = None
    transaction_id: Optional[str] = None


def _run(fn, *args, **kwargs):
    """Map workflow errors to HTTP status codes."""
    try:
        return fn(*args, **kwargs)
    except LookupError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("", response_model=Dict[str, Any], status_code=status.HTTP_201_CREATED)
async def create_advance_booking(request: CreateAdvanceBookingRequest, current_user: CurrentUser):
    """
    Create pre-harvest booking with quality standards and contract terms

    - Calculates the advance payment from the percentage and quantity
    - Stores the booking as "pending" until the farmer confirms it
    """
    booking = _run(
        booking_workflow.create,
        current_user,
        request.listing_id,
        request.quantity_booked,
        request.price_per_unit,
        request.advance_payment_percent,
        request.expected_delivery_date,
        request.quality_standards.model_dump(),
        request.contract_terms.model_dump(),
    )
    return {"success": True, "message": "Advance booking created successfully", "booking": booking}


@router.get("", response_model=Dict[str, Any])
async def list_bookings(
    current_user: CurrentUser, role: Optional[str] = None, status: Optional[str] = None
):
    """List your bookings; role=buyer or role=farmer narrows to one side."""
    bookings = booking_workflow.list_for(current_user, role, status)
    return {"success": True, "count": len(bookings), "bookings": bookings}


@router.get("/{id}", response_model=Dict[str, Any])
async def get_booking(id: int, current_user: CurrentUser):
    """Booking with its listing, payment milestones and quality checks"""
    return {"success": True, **_run(booking_workflow.detail, id, current_user)}


@router.put("/{id}", response_model=Dict[str, Any])
async def update_booking_status(id: int, request: StatusUpdateRequest, current_user: CurrentUser):
    """Move a booking along: confirmed (farmer), cancelled (either side), completed (buyer)"""
    actions = {
        "confirmed": booking_workflow.confirm,
        "cancelled": booking_workflow.cancel,
        "completed": booking_workflow.complete,
    }
    if request.status not in actions:
        raise HTTPException(status_code=400, detail=f"Unsupported status '{request.status}'")
    return {"success": True, "booking": _run(actions[request.status], id, current_user)}


@router.post("/{id}/confirm", response_model=Dict[str, Any])
async def confirm_booking(id: int, current_user: CurrentUser):
    """Farmer confirms: reserves the quantity on the listing and schedules payment milestones"""
    return {
        "success": True,
        "message": "Booking confirmed successfully",
        "booking": _run(booking_workflow.confirm, id, current_user),
    }


@router.post("/{id}/cancel", response_model=Dict[str, Any])
async def cancel_booking(id: int, current_user: CurrentUser):
    """Cancel booking and restore listing available quantity"""
    return {
        "success": True,
        "message": "Booking cancelled successfully",
        "booking": _run(booking_workflow.cancel, id, current_user),
    }


@router.post("/{id}/complete", response_model=Dict[str, Any])
async def complete_booking(id: int, current_user: CurrentUser):
    """Buyer marks the booking complete (handover occurred)"""
    return {"success": True, "booking": _run(booking_workflow.complete, id, current_user)}


@router.post("/{id}/quality-verify", response_model=Dict[str, Any])
async def quality_verify(
    id: int, current_user: CurrentUser, request: Optional[QualityVerificationRequest] = None
):
    """Record a quality check; a failed check moves the booking to "disputed"."""
    r = request or QualityVerificationRequest(quality_grade="A")
    booking = _run(
        booking_workflow.verify_quality,
        id,
        current_user,
        r.verifier_type,
        r.quality_grade,
        r.quality_metrics,
        r.photos,
        r.passed,
        r.notes,
    )
    return {"success": True, "booking": booking}


@router.post("/{id}/dispute", response_model=Dict[str, Any])
async def raise_dispute(id: int, request: DisputeRequest, current_user: CurrentUser):
    """Raise a quality/delivery dispute on a booking"""
    booking = _run(
        booking_workflow.dispute,
        id,
        current_user,
        request.dispute_reason,
        request.details,
        request.photos,
    )
    return {"success": True, "message": "Dispute submitted", "booking": booking}


@router.post("/{id}/payments", response_model=Dict[str, Any])
async def record_payment(id: int, request: PaymentRequest, current_user: CurrentUser):
    """Buyer records payment of the next pending milestone of a type"""
    milestone = _run(
        booking_workflow.record_payment,
        id,
        current_user,
        request.milestone_type,
        request.payment_method,
        request.transaction_id,
    )
    return {"success": True, "milestone": milestone}
