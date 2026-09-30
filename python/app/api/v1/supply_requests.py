"""
Supply Request API Endpoints
Handles buyer supply requests and AI-powered matching with farmer listings
"""

from datetime import datetime
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.core.auth import get_current_active_user
from app.services.supply_request_matching_service import SupplyRequestMatchingService

router = APIRouter(
    prefix="/supply-requests",
    tags=["supply-requests"],
    dependencies=[Depends(get_current_active_user)],
)


class SupplyRequestCreate(BaseModel):
    """Schema for creating a supply request"""

    buyer_id: int = Field(..., description="ID of the buyer")
    crop_type: str = Field(..., description="Type of crop needed")
    quantity_needed: float = Field(..., gt=0, description="Quantity needed in kg")
    quality_requirements: Optional[str] = Field(None, description="Quality specifications")
    delivery_date_start: datetime = Field(..., description="Earliest delivery date")
    delivery_date_end: datetime = Field(..., description="Latest delivery date")
    max_price_per_unit: Optional[float] = Field(None, description="Maximum price per kg")
    recurring: bool = Field(False, description="Is this a recurring request")
    recurrence_pattern: Optional[str] = Field(
        None, description="Recurrence pattern (weekly, monthly)"
    )
    is_emergency: bool = Field(False, description="Is this an emergency request")
    delivery_address: Optional[str] = Field(None, description="Delivery address")
    delivery_latitude: Optional[float] = Field(None, description="Delivery latitude")
    delivery_longitude: Optional[float] = Field(None, description="Delivery longitude")
    delivery_pincode: Optional[str] = Field(None, description="Delivery pincode")
    delivery_state: Optional[str] = Field(None, description="Delivery state")
    delivery_district: Optional[str] = Field(None, description="Delivery district")
    notes: Optional[str] = Field(None, description="Additional notes")


class MatchAcceptance(BaseModel):
    """Schema for accepting a match"""

    match_id: Optional[int] = Field(None, description="ID of single match to accept")
    aggregation_group_id: Optional[str] = Field(
        None, description="ID of aggregated group to accept"
    )


def get_matching_service() -> SupplyRequestMatchingService:
    """Dependency to get matching service instance"""
    return SupplyRequestMatchingService()


@router.post("/", response_model=Dict[str, Any], status_code=201)
async def create_supply_request(
    request: SupplyRequestCreate,
    service: SupplyRequestMatchingService = Depends(get_matching_service),
):
    """
    Create a new supply request and get initial AI-powered matches

    This endpoint:
    1. Creates a supply request in the database
    2. Finds available farmer listings for the crop type
    3. Uses Amazon Bedrock AI to match supply with demand
    4. Returns the request ID and initial matches

    Returns:
        - request_id: ID of the created supply request
        - initial_matches: AI-matched supply options
        - status: Request status (open, filled, etc.)
    """
    try:
        result = service.create_supply_request(request.dict())
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create supply request: {str(e)}")


@router.get("/{request_id}/matches", response_model=Dict[str, Any])
async def get_supply_matches(
    request_id: int, service: SupplyRequestMatchingService = Depends(get_matching_service)
):
    """
    Get AI-matched supply options for a supply request

    Returns:
        - single_farmer_matches: Farmers who can fulfill the entire order
        - aggregated_options: Multi-farmer combinations to meet the requirement
        - Each match includes:
          - match_score (0-100): AI-calculated compatibility score
          - price_offered: Price per unit
          - matched_quantity: Quantity available
          - explanation: Why this is a good match
    """
    try:
        matches = service.get_matches_for_request(request_id)
        return matches
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get matches: {str(e)}")


@router.post("/{request_id}/accept-match", response_model=Dict[str, Any])
async def accept_supply_match(
    request_id: int,
    acceptance: MatchAcceptance,
    service: SupplyRequestMatchingService = Depends(get_matching_service),
):
    """
    Accept a supply match and create booking(s)

    For single farmer match:
    - Provide match_id
    - Creates one advance booking

    For aggregated match:
    - Provide aggregation_group_id
    - Creates multiple advance bookings (one per farmer)

    Returns:
        - success: Boolean indicating success
        - booking_ids: List of created booking IDs
        - message: Success message
    """
    try:
        if not acceptance.match_id and not acceptance.aggregation_group_id:
            raise HTTPException(
                status_code=400, detail="Either match_id or aggregation_group_id must be provided"
            )

        result = service.accept_match(
            request_id=request_id,
            match_id=acceptance.match_id,
            aggregation_group_id=acceptance.aggregation_group_id,
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to accept match: {str(e)}")


@router.post("/{request_id}/refresh-matches", response_model=Dict[str, Any])
async def refresh_supply_matches(
    request_id: int, service: SupplyRequestMatchingService = Depends(get_matching_service)
):
    """
    Refresh AI matches for a supply request

    Useful when:
    - New farmer listings become available
    - Buyer wants to see updated matches
    - Previous matches were rejected

    Returns updated matches with current availability
    """
    try:
        matches = service.find_matches(request_id)
        return matches
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to refresh matches: {str(e)}")


class FarmerConfirmation(BaseModel):
    """Schema for farmer confirmation"""

    farmer_id: int = Field(..., description="ID of the farmer")
    confirmation: bool = Field(..., description="True to accept, False to reject")
    notes: Optional[str] = Field(None, description="Optional notes from farmer")


class DeliveryStatusUpdate(BaseModel):
    """Schema for delivery status update"""

    delivery_status: str = Field(
        ..., description="Delivery status (pending, in_transit, delivered, failed)"
    )
    notes: Optional[str] = Field(None, description="Optional delivery notes")


@router.post("/{request_id}/matches/{match_id}/farmer-confirm", response_model=Dict[str, Any])
async def farmer_confirm_match(
    request_id: int,
    match_id: int,
    confirmation: FarmerConfirmation,
    service: SupplyRequestMatchingService = Depends(get_matching_service),
):
    """
    Farmer confirms or rejects a match acceptance

    When a buyer accepts a match, the farmer receives a notification and must
    confirm or reject the match within 24 hours.

    Args:
        request_id: ID of the supply request
        match_id: ID of the match
        confirmation: Farmer's confirmation (accept/reject) with optional notes

    Returns:
        - success: Boolean indicating success
        - status: confirmed or rejected
        - next_steps: List of next actions
        - confirmation_timestamp: When farmer confirmed
    """
    try:
        result = service.farmer_confirm_match(
            match_id=match_id,
            farmer_id=confirmation.farmer_id,
            confirmation=confirmation.confirmation,
            notes=confirmation.notes,
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to process farmer confirmation: {str(e)}"
        )


@router.get("/{request_id}/coordination-status", response_model=Dict[str, Any])
async def get_coordination_status(
    request_id: int, service: SupplyRequestMatchingService = Depends(get_matching_service)
):
    """
    Get coordination status for a supply request

    Shows:
    - Farmer confirmation status for all matches
    - Delivery status tracking
    - Payment milestone status
    - Multi-farmer coordination details

    Useful for:
    - Buyers to track order fulfillment
    - Coordinating multi-farmer deliveries
    - Monitoring payment and delivery progress

    Returns:
        - request_status: Overall request status
        - single_farmer_matches: List of single farmer matches with status
        - aggregated_groups: Multi-farmer coordination groups with status
        - Each match includes: farmer_confirmation, delivery_status, payment_status
    """
    try:
        status = service.get_coordination_status(request_id)
        return status
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get coordination status: {str(e)}")


@router.put("/{request_id}/matches/{match_id}/delivery-status", response_model=Dict[str, Any])
async def update_delivery_status(
    request_id: int,
    match_id: int,
    status_update: DeliveryStatusUpdate,
    service: SupplyRequestMatchingService = Depends(get_matching_service),
):
    """
    Update delivery status for a match

    Delivery statuses:
    - pending: Awaiting delivery
    - in_transit: Delivery in progress
    - delivered: Successfully delivered
    - failed: Delivery failed

    Args:
        request_id: ID of the supply request
        match_id: ID of the match
        status_update: New delivery status and optional notes

    Returns:
        - success: Boolean indicating success
        - delivery_status: Updated status
        - message: Status message
    """
    try:
        result = service.update_delivery_status(
            match_id=match_id,
            delivery_status=status_update.delivery_status,
            notes=status_update.notes,
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update delivery status: {str(e)}")
