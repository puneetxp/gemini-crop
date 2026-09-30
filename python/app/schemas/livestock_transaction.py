"""
Livestock Transaction Schemas

Pydantic models for livestock transaction validation and serialization.
Supports transaction workflow (inquiry, negotiation, agreed, completed),
messaging between buyers and sellers, and health guarantee system.

Compatible with Python 3.14.3, Pydantic 2.10.5
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator


class TransactionTypeEnum(str, Enum):
    """Transaction types"""

    SALE = "sale"
    BREEDING = "breeding"
    LEASE = "lease"


class TransactionStatusEnum(str, Enum):
    """Transaction status workflow"""

    INQUIRY = "inquiry"
    NEGOTIATION = "negotiation"
    AGREED = "agreed"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class LivestockTransactionBase(BaseModel):
    """Base livestock transaction schema"""

    listing_id: int = Field(..., description="ID of the livestock listing")
    transaction_type: TransactionTypeEnum = Field(..., description="Type of transaction")
    quantity: int = Field(1, ge=1, le=1000, description="Number of animals")
    buyer_message: Optional[str] = Field(
        None, max_length=2000, description="Initial inquiry message"
    )
    buyer_contact_phone: Optional[str] = Field(
        None, max_length=20, description="Buyer contact phone"
    )
    buyer_contact_email: Optional[str] = Field(
        None, max_length=255, description="Buyer contact email"
    )
    delivery_required: bool = Field(False, description="Whether delivery is required")
    delivery_address: Optional[str] = Field(None, max_length=500, description="Delivery address")
    delivery_latitude: Optional[float] = Field(
        None, ge=-90, le=90, description="Delivery GPS latitude"
    )
    delivery_longitude: Optional[float] = Field(
        None, ge=-180, le=180, description="Delivery GPS longitude"
    )


class LivestockTransactionCreate(LivestockTransactionBase):
    """Schema for creating a livestock transaction (buyer initiates)"""

    # Ignored by the API: the buyer is the signed-in user and the seller comes from the listing.
    buyer_id: Optional[int] = Field(None, description="Ignored; the signed-in user is the buyer")
    seller_id: Optional[int] = Field(None, description="Ignored; taken from the listing")

    @field_validator("buyer_message")
    @classmethod
    def validate_message(cls, v):
        if v and len(v.strip()) < 10:
            raise ValueError("Message must be at least 10 characters")
        return v


class LivestockTransactionUpdate(BaseModel):
    """Schema for updating a livestock transaction"""

    status: Optional[TransactionStatusEnum] = None
    agreed_price: Optional[float] = Field(None, gt=0, description="Agreed price in INR")
    seller_response: Optional[str] = Field(
        None, max_length=2000, description="Seller response message"
    )
    buyer_message: Optional[str] = Field(None, max_length=2000, description="Updated buyer message")
    delivery_required: Optional[bool] = None
    delivery_address: Optional[str] = Field(None, max_length=500)
    delivery_latitude: Optional[float] = Field(None, ge=-90, le=90)
    delivery_longitude: Optional[float] = Field(None, ge=-180, le=180)
    notes: Optional[str] = Field(None, max_length=1000, description="Additional notes")


class LivestockTransactionResponse(LivestockTransactionBase):
    """Schema for livestock transaction response"""

    id: int
    seller_id: int
    buyer_id: int
    status: TransactionStatusEnum
    agreed_price: Optional[float] = None
    seller_response: Optional[str] = None
    health_guarantee_days: int = 7
    health_guarantee_expires: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    cancelled_at: Optional[datetime] = None
    cancellation_reason: Optional[str] = None
    notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class LivestockTransactionWithDetails(LivestockTransactionResponse):
    """Transaction response with listing and user details"""

    listing: Optional[Dict[str, Any]] = None
    seller: Optional[Dict[str, Any]] = None
    buyer: Optional[Dict[str, Any]] = None


class TransactionMessageCreate(BaseModel):
    """Schema for adding a message to a transaction"""

    transaction_id: int = Field(..., description="Transaction ID")
    message: str = Field(..., min_length=10, max_length=2000, description="Message content")
    is_seller: bool = Field(..., description="True if message is from seller, False if from buyer")


class TransactionStatusUpdate(BaseModel):
    """Schema for updating transaction status"""

    status: TransactionStatusEnum = Field(..., description="New status")
    message: Optional[str] = Field(
        None, max_length=2000, description="Optional message with status update"
    )
    agreed_price: Optional[float] = Field(
        None, gt=0, description="Agreed price (required for 'agreed' status)"
    )

    @field_validator("agreed_price")
    @classmethod
    def validate_agreed_price(cls, v, info):
        if info.data.get("status") == TransactionStatusEnum.AGREED and not v:
            raise ValueError("Agreed price is required when status is 'agreed'")
        return v


class TransactionCancellation(BaseModel):
    """Schema for cancelling a transaction"""

    cancellation_reason: str = Field(
        ..., min_length=10, max_length=500, description="Reason for cancellation"
    )


class TransactionCompletion(BaseModel):
    """Schema for completing a transaction"""

    notes: Optional[str] = Field(None, max_length=1000, description="Completion notes")


class TransactionSearchFilters(BaseModel):
    """Search filters for transactions"""

    listing_id: Optional[int] = None
    seller_id: Optional[int] = None
    buyer_id: Optional[int] = None
    transaction_type: Optional[TransactionTypeEnum] = None
    status: Optional[TransactionStatusEnum] = None
    min_price: Optional[float] = Field(None, ge=0)
    max_price: Optional[float] = Field(None, ge=0)
    created_after: Optional[datetime] = None
    created_before: Optional[datetime] = None
    skip: int = Field(0, ge=0)
    limit: int = Field(20, ge=1, le=100)
    sort_by: str = Field("created_at", pattern="^(created_at|agreed_price|status)$")
    sort_order: str = Field("desc", pattern="^(asc|desc)$")


class TransactionAnalytics(BaseModel):
    """Analytics for transactions"""

    total_transactions: int
    by_status: Dict[str, int]
    by_type: Dict[str, int]
    total_value: float
    average_transaction_value: float
    completion_rate: float
    cancellation_rate: float
    average_time_to_completion_days: Optional[float] = None


class BulkTransactionCreate(BaseModel):
    """Schema for creating bulk transactions (multiple animals from same listing)"""

    listing_id: int = Field(..., description="ID of the livestock listing")
    transaction_type: TransactionTypeEnum = Field(..., description="Type of transaction")
    quantities: List[int] = Field(
        ..., min_length=1, max_length=10, description="List of quantities for each transaction"
    )
    buyer_message: Optional[str] = Field(
        None, max_length=2000, description="Initial inquiry message"
    )
    buyer_contact_phone: Optional[str] = Field(None, max_length=20)
    buyer_contact_email: Optional[str] = Field(None, max_length=255)
    delivery_required: bool = Field(False)
    delivery_address: Optional[str] = Field(None, max_length=500)
    delivery_latitude: Optional[float] = Field(None, ge=-90, le=90)
    delivery_longitude: Optional[float] = Field(None, ge=-180, le=180)

    @field_validator("quantities")
    @classmethod
    def validate_quantities(cls, v):
        if sum(v) > 1000:
            raise ValueError("Total quantity cannot exceed 1000")
        if any(q < 1 for q in v):
            raise ValueError("Each quantity must be at least 1")
        return v


class TransactionHistoryResponse(BaseModel):
    """Transaction history for a user"""

    user_id: int
    role: str = Field(..., pattern="^(buyer|seller)$", description="User role in transactions")
    transactions: List[LivestockTransactionResponse]
    total_count: int
    total_value: float
    completed_count: int
    cancelled_count: int
    active_count: int
