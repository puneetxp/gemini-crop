"""
Market Intelligence API Endpoints
Provides price tracking, trends, and analytics
"""

from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import get_current_admin
from app.core.database import get_db
from app.orm.market_price import MarketPrice
from app.services.price_tracking_service import PriceTrackingService

router = APIRouter(prefix="/market-intelligence", tags=["market-intelligence"])


@router.post("/collect/listing/{listing_id}", dependencies=[Depends(get_current_admin)])
async def collect_price_from_listing(listing_id: int, db: AsyncSession = Depends(get_db)):
    """
    Collect price data from a marketplace listing

    Args:
        listing_id: ID of the marketplace listing

    Returns:
        Created market price record
    """
    service = PriceTrackingService(db)
    price_data = await service.collect_price_from_listing(listing_id)

    if not price_data:
        raise HTTPException(status_code=404, detail="Listing not found or has no price data")

    return {"success": True, "message": "Price data collected successfully", "data": price_data}


@router.post("/collect/booking/{booking_id}", dependencies=[Depends(get_current_admin)])
async def collect_price_from_booking(booking_id: int, db: AsyncSession = Depends(get_db)):
    """
    Collect price data from an advance booking

    Args:
        booking_id: ID of the advance booking

    Returns:
        Created market price record
    """
    service = PriceTrackingService(db)
    price_data = await service.collect_price_from_booking(booking_id)

    if not price_data:
        raise HTTPException(status_code=404, detail="Booking not found")

    return {"success": True, "message": "Price data collected from booking", "data": price_data}


@router.post(
    "/collect/livestock-transaction/{transaction_id}", dependencies=[Depends(get_current_admin)]
)
async def collect_price_from_livestock_transaction(
    transaction_id: int, db: AsyncSession = Depends(get_db)
):
    """
    Collect price data from a livestock transaction

    Args:
        transaction_id: ID of the livestock transaction

    Returns:
        Created market price record
    """
    service = PriceTrackingService(db)
    price_data = await service.collect_price_from_livestock_transaction(transaction_id)

    if not price_data:
        raise HTTPException(status_code=404, detail="Transaction not found or not completed")

    return {
        "success": True,
        "message": "Price data collected from livestock transaction",
        "data": price_data,
    }


@router.get("/price-history")
async def price_history_alias(
    item_type: str = Query(..., description="Type of item"),
    item_name: str = Query(..., description="Name of the item"),
    db: AsyncSession = Depends(get_db),
):
    """Registry alias for price history"""
    return await get_price_trends(item_type, item_name, state=None, district=None, days=90, db=db)


@router.get("/trends/{item_type}/{item_name}")
async def get_price_trends(
    item_type: str,
    item_name: str,
    state: Optional[str] = None,
    district: Optional[str] = None,
    days: int = Query(90, ge=7, le=365, description="Number of days to analyze"),
    db: AsyncSession = Depends(get_db),
):
    """
    Get price trends for an item

    Args:
        item_type: Type of item (crop, livestock)
        item_name: Name of the item
        state: Optional state filter
        district: Optional district filter
        days: Number of days to look back (7-365)

    Returns:
        Price trend analysis with time series data
    """
    service = PriceTrackingService(db)
    trends = await service.get_price_trends(
        item_type=item_type, item_name=item_name, state=state, district=district, days=days
    )

    return {"success": True, "data": trends}


@router.get("/quality-premiums/{item_type}/{item_name}")
async def get_quality_premiums(
    item_type: str,
    item_name: str,
    state: Optional[str] = None,
    days: int = Query(90, ge=7, le=365, description="Number of days to analyze"),
    db: AsyncSession = Depends(get_db),
):
    """
    Get quality premium analysis by grade

    Args:
        item_type: Type of item (crop, livestock)
        item_name: Name of the item
        state: Optional state filter
        days: Number of days to look back (7-365)

    Returns:
        Quality premium analysis by grade
    """
    service = PriceTrackingService(db)
    premiums = await service.get_quality_premiums(
        item_type=item_type, item_name=item_name, state=state, days=days
    )

    return {"success": True, "data": premiums}


@router.get("/demand-forecast/{item_type}/{item_name}")
async def get_demand_forecast(
    item_type: str,
    item_name: str,
    state: Optional[str] = None,
    days_ahead: int = Query(30, ge=7, le=90, description="Days to forecast"),
    db: AsyncSession = Depends(get_db),
):
    """
    Get demand forecast based on booking patterns

    Args:
        item_type: Type of item (crop, livestock)
        item_name: Name of the item
        state: Optional state filter
        days_ahead: Number of days to forecast (7-90)

    Returns:
        Demand forecast with confidence score
    """
    service = PriceTrackingService(db)
    forecast = await service.get_demand_forecast(
        item_type=item_type, item_name=item_name, state=state, days_ahead=days_ahead
    )

    return {"success": True, "data": forecast}


@router.get("/price-tracking")
async def price_tracking_alias(db: AsyncSession = Depends(get_db)):
    """Registry alias for price tracking"""
    return await get_market_prices(limit=100, offset=0, db=db)


@router.get("/prices")
async def get_market_prices(
    item_type: Optional[str] = None,
    item_name: Optional[str] = None,
    state: Optional[str] = None,
    district: Optional[str] = None,
    source: Optional[str] = None,
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    """
    Get market price records with filters

    Args:
        item_type: Optional item type filter
        item_name: Optional item name filter
        state: Optional state filter
        district: Optional district filter
        source: Optional source filter (marketplace, booking, livestock_transaction)
        limit: Maximum number of records (1-500)
        offset: Offset for pagination

    Returns:
        List of market price records
    """
    # Get all prices and filter
    from app.services.price_tracking_service import _all_prices

    all_prices = await _all_prices()

    prices = []
    for p in all_prices:
        if item_type and p["item_type"] != item_type:
            continue
        if item_name and p["item_name"] != item_name:
            continue
        if state and p["state"] != state:
            continue
        if district and p["district"] != district:
            continue
        if source and p["source"] != source:
            continue
        prices.append(p)

    # Apply pagination
    total = len(prices)
    prices = prices[offset : offset + limit]

    return {"success": True, "total": total, "limit": limit, "offset": offset, "data": prices}


@router.get("/dashboard")
async def market_dashboard_alias(db: AsyncSession = Depends(get_db)):
    """Registry alias for market dashboard"""
    return await get_market_summary(db=db)


@router.get("/summary")
async def get_market_summary(state: Optional[str] = None, db: AsyncSession = Depends(get_db)):
    """
    Get market summary statistics

    Args:
        state: Optional state filter

    Returns:
        Market summary with key statistics
    """
    # Get all prices and filter
    from app.services.price_tracking_service import _all_prices

    all_prices = await _all_prices()

    prices = []
    for p in all_prices:
        if state and p["state"] != state:
            continue
        prices.append(p)

    if not prices:
        return {
            "success": True,
            "data": {"total_transactions": 0, "total_value": 0, "crops": {}, "livestock": {}},
        }

    # Calculate summary statistics
    total_value = sum(p["total_value"] for p in prices)

    # Group by item type
    crops = {}
    livestock = {}

    for price in prices:
        if price["item_type"] == "crop":
            item = price["item_name"]
            if item not in crops:
                crops[item] = {"transactions": 0, "total_volume": 0, "avg_price": 0, "prices": []}
            crops[item]["transactions"] += 1
            crops[item]["total_volume"] += price["quantity"]
            crops[item]["prices"].append(price["price_per_unit"])

        elif price["item_type"] == "livestock":
            item = price["item_name"]
            if item not in livestock:
                livestock[item] = {
                    "transactions": 0,
                    "total_animals": 0,
                    "avg_price": 0,
                    "prices": [],
                }
            livestock[item]["transactions"] += 1
            livestock[item]["total_animals"] += price["quantity"]
            livestock[item]["prices"].append(price["price_per_unit"])

    # Calculate averages
    for item, data in crops.items():
        data["avg_price"] = round(sum(data["prices"]) / len(data["prices"]), 2)
        del data["prices"]

    for item, data in livestock.items():
        data["avg_price"] = round(sum(data["prices"]) / len(data["prices"]), 2)
        del data["prices"]

    return {
        "success": True,
        "data": {
            "total_transactions": len(prices),
            "total_value": round(total_value, 2),
            "crops": crops,
            "livestock": livestock,
        },
    }


@router.get("/msp")
async def get_msp_rates(
    crop_name: Optional[str] = None,
    year: Optional[int] = None,
    season: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    """
    Get Minimum Support Price (MSP) rates for crops
    """
    from app.orm.msp_rate import MspRate

    filters = {"enable": 1}
    if crop_name:
        filters["crop_name"] = crop_name
    if year:
        filters["year"] = int(year)
    if season:
        filters["season"] = season

    from app.core.db import DB

    where = " AND ".join(f'"{k}" = ?' for k in filters)
    results = [
        {k: float(v) if hasattr(v, "is_finite") else v for k, v in r.items()}
        for r in DB.raw(
            f"SELECT * FROM msp_rates WHERE {where} ORDER BY year DESC, crop_name",
            list(filters.values()),
        ).result
    ]
    return {"success": True, "data": results}
