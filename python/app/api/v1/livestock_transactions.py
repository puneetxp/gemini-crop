"""
Livestock Transaction API Endpoints

RESTful API for livestock transaction workflow including:
- Transaction initiation (buyer inquiry)
- Messaging between buyers and sellers
- Status tracking and updates
- Transaction completion and cancellation
- Bulk trading support
- Transaction history and analytics

Business rules live in app/services/livestock_trade_workflow.py. Every endpoint acts as the signed-in
user: only the buyer and seller on a transaction (or an admin) can see or change it.
"""

import logging
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from app.core.auth import get_current_active_user
from app.schemas.livestock_transaction import (
    BulkTransactionCreate,
    LivestockTransactionCreate,
    LivestockTransactionResponse,
    LivestockTransactionUpdate,
    LivestockTransactionWithDetails,
    TransactionAnalytics,
    TransactionCancellation,
    TransactionCompletion,
    TransactionHistoryResponse,
    TransactionStatusEnum,
    TransactionStatusUpdate,
    TransactionTypeEnum,
)
from app.services.livestock_trade_workflow import livestock_trade_workflow as trades
from app.services.notification_service import get_notification_service

logger = logging.getLogger(__name__)
router = APIRouter(
    prefix="/livestock-transactions",
    tags=["livestock-transactions"],
    dependencies=[Depends(get_current_active_user)],
)


def _run(fn, *args, **kwargs):
    """Map workflow errors to HTTP status codes."""
    try:
        return fn(*args, **kwargs)
    except LookupError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


def _notify(t: dict, notification_type: str, extra: Optional[dict] = None) -> None:
    """Tell the other party; a failed notification never fails the request."""
    try:
        get_notification_service().send_livestock_transaction_notification(
            transaction_id=t["id"],
            seller_id=t["seller_id"],
            buyer_id=t["buyer_id"],
            listing_id=t["listing_id"],
            notification_type=notification_type,
            extra_data=extra,
        )
    except Exception as e:
        logger.warning(f"Failed to send {notification_type} notification: {e}")


@router.post("", response_model=LivestockTransactionResponse, status_code=201)
async def create_transaction(
    transaction: LivestockTransactionCreate, current_user=Depends(get_current_active_user)
):
    """
    Initiate a new livestock transaction (buyer inquiry)

    Creates a transaction in 'inquiry' status and notifies the seller.
    """
    result = _run(
        trades.initiate,
        current_user,
        transaction.listing_id,
        transaction.transaction_type.value,
        transaction.quantity,
        **transaction.model_dump(
            exclude={"listing_id", "transaction_type", "quantity", "buyer_id", "seller_id"}
        ),
    )
    _notify(result, "new_inquiry")
    return result


@router.post("/bulk", response_model=List[LivestockTransactionResponse], status_code=201)
async def create_bulk_transactions(
    bulk_request: BulkTransactionCreate, current_user=Depends(get_current_active_user)
):
    """
    Create multiple transactions for bulk trading

    Useful when buying multiple animals from the same listing.
    """
    results = _run(
        trades.initiate_bulk,
        current_user,
        bulk_request.listing_id,
        bulk_request.transaction_type.value,
        bulk_request.quantities,
        **bulk_request.model_dump(exclude={"listing_id", "transaction_type", "quantities"}),
    )
    _notify(results[0], "bulk_inquiry", {"total_quantity": sum(bulk_request.quantities)})
    return results


# Static paths first so they aren't captured by /{id}.
@router.get("/analytics", response_model=TransactionAnalytics)
async def get_transaction_analytics(
    role: Optional[str] = Query(None, pattern="^(buyer|seller)$"),
    user_id: Optional[int] = Query(
        None, description="Admins only: another user's analytics; omit for platform-wide"
    ),
    current_user=Depends(get_current_active_user),
):
    """Your transaction analytics (admins: any user's, or platform-wide when user_id is omitted)"""
    is_admin = getattr(current_user, "user_type", None) == "admin"
    return trades.analytics(user_id if is_admin else current_user.id, role)


@router.get("/user/{user_id}/history", response_model=TransactionHistoryResponse)
async def get_user_transaction_history(
    user_id: int,
    role: str = Query(..., pattern="^(buyer|seller)$"),
    status: Optional[TransactionStatusEnum] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    current_user=Depends(get_current_active_user),
):
    """
    Get transaction history for a user (as buyer or seller)
    """
    if user_id != current_user.id and getattr(current_user, "user_type", None) != "admin":
        raise HTTPException(
            status_code=403, detail="You can only view your own transaction history"
        )
    transactions = trades.history(user_id, role, status.value if status else None, skip, limit)
    return {
        "user_id": user_id,
        "role": role,
        "transactions": transactions,
        "total_count": len(transactions),
        "total_value": sum(
            float(t["agreed_price"] or 0) for t in transactions if t["status"] == "completed"
        ),
        "completed_count": sum(1 for t in transactions if t["status"] == "completed"),
        "cancelled_count": sum(1 for t in transactions if t["status"] == "cancelled"),
        "active_count": sum(
            1 for t in transactions if t["status"] in ("inquiry", "negotiation", "agreed")
        ),
    }


@router.get("", response_model=List[LivestockTransactionResponse])
async def list_transactions(
    listing_id: Optional[int] = Query(None),
    transaction_type: Optional[TransactionTypeEnum] = Query(None),
    status: Optional[TransactionStatusEnum] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    current_user=Depends(get_current_active_user),
):
    """
    List your transactions (as buyer or seller) with optional filters
    """
    filters = {}
    if listing_id:
        filters["listing_id"] = listing_id
    if transaction_type:
        filters["transaction_type"] = transaction_type.value
    if status:
        filters["status"] = status.value
    return trades.list_for(current_user, filters, skip, limit)


@router.get("/{id}", response_model=LivestockTransactionWithDetails)
async def get_transaction(id: int, current_user=Depends(get_current_active_user)):
    """
    Get transaction details with listing and user information
    """
    return _run(trades.detail, id, current_user)


@router.put("/{id}", response_model=LivestockTransactionResponse)
async def update_transaction(
    id: int, update: LivestockTransactionUpdate, current_user=Depends(get_current_active_user)
):
    """
    Update transaction details (agreed price / status / message)
    """
    message = update.seller_response or update.buyer_message or update.notes
    result = _run(
        trades.update_status,
        id,
        current_user,
        update.status.value if update.status else None,
        update.agreed_price,
        message,
    )
    _notify(result, "status_update", {"new_status": result["status"]})
    return result


@router.put("/{id}/status", response_model=LivestockTransactionResponse)
async def update_transaction_status(
    id: int, status_update: TransactionStatusUpdate, current_user=Depends(get_current_active_user)
):
    """
    Update transaction status

    Status flow: inquiry → negotiation → agreed → completed
    Can also move to cancelled from any open status.
    """
    result = _run(
        trades.update_status,
        id,
        current_user,
        status_update.status.value,
        status_update.agreed_price,
        status_update.message,
    )
    _notify(result, "status_update", {"new_status": status_update.status.value})
    return result


@router.post("/{transaction_id}/seller-response", response_model=LivestockTransactionResponse)
async def add_seller_response(
    transaction_id: int,
    message: str = Query(..., min_length=10, max_length=2000),
    new_status: Optional[TransactionStatusEnum] = Query(None),
    current_user=Depends(get_current_active_user),
):
    """
    Add seller response message to a transaction

    Optionally update status (e.g., from inquiry to negotiation).
    """
    result = _run(
        trades.seller_reply,
        transaction_id,
        current_user,
        message,
        new_status.value if new_status else None,
    )
    _notify(result, "seller_response")
    return result


@router.post("/{transaction_id}/buyer-message", response_model=LivestockTransactionResponse)
async def add_buyer_message(
    transaction_id: int,
    message: str = Query(..., min_length=10, max_length=2000),
    current_user=Depends(get_current_active_user),
):
    """
    Add buyer message to a transaction
    """
    result = _run(trades.buyer_message, transaction_id, current_user, message)
    _notify(result, "buyer_message")
    return result


@router.post("/{transaction_id}/complete", response_model=LivestockTransactionResponse)
async def complete_transaction(
    transaction_id: int,
    completion: TransactionCompletion,
    current_user=Depends(get_current_active_user),
):
    """
    Complete a transaction (seller confirms delivery/handover)

    Activates the health guarantee period (7 days by default).
    """
    result = _run(trades.complete, transaction_id, current_user, completion.notes)
    _notify(
        result,
        "completed",
        {"health_guarantee_expires": result["health_guarantee_expires"].isoformat()},
    )
    return result


@router.post("/{transaction_id}/cancel", response_model=LivestockTransactionResponse)
async def cancel_transaction(
    transaction_id: int,
    cancellation: TransactionCancellation,
    current_user=Depends(get_current_active_user),
):
    """
    Cancel a transaction

    Can be done by either buyer or seller.
    """
    result = _run(trades.cancel, transaction_id, current_user, cancellation.cancellation_reason)
    _notify(result, "cancelled", {"cancellation_reason": cancellation.cancellation_reason})
    return result
