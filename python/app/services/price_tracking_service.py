"""
Price Tracking Service
Collects and analyzes price data from marketplace transactions
"""

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.orm.advance_booking import AdvanceBooking
from app.orm.livestock_transaction import LivestockTransaction
from app.orm.market_price import MarketPrice
from app.orm.marketplace_listing import MarketplaceListing


# The ORM classes have no async API; these helpers read/write with parameterised SQL.
def _row(row: Dict[str, Any]) -> Dict[str, Any]:
    from decimal import Decimal

    return {k: float(v) if isinstance(v, Decimal) else v for k, v in row.items()}


async def _find(table: str, item_id: int) -> Optional[Dict[str, Any]]:
    from app.core.db import DB

    rows = DB.raw(f'SELECT * FROM "{table}" WHERE id = ?', [item_id]).result
    return _row(rows[0]) if rows else None


async def _all_prices(where: str = "", bind: Optional[list] = None) -> List[Dict[str, Any]]:
    from app.core.db import DB

    sql = (
        "SELECT * FROM market_prices"
        + (f" WHERE {where}" if where else "")
        + " ORDER BY transaction_date"
    )
    return [_row(r) for r in DB.raw(sql, bind or []).result]


async def _create_price(data: Dict[str, Any]) -> Dict[str, Any]:
    from app.core.db import DB

    cols = ", ".join(f'"{k}"' for k in data)
    marks = ", ".join("?" for _ in data)
    return _row(
        DB.raw(
            f"INSERT INTO market_prices ({cols}) VALUES ({marks}) RETURNING *", list(data.values())
        ).result[0]
    )


class PriceTrackingService:
    """Service for tracking and analyzing market prices"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def collect_price_from_listing(self, listing_id: int) -> Optional[Dict[str, Any]]:
        """
        Collect price data from a marketplace listing

        Args:
            listing_id: ID of the marketplace listing

        Returns:
            Created market price record or None
        """
        # Get listing details
        listing = await _find("marketplace_listings", listing_id)
        if not listing or not listing.get("price_per_unit"):
            return None

        # Create market price record
        price_data = {
            "listing_id": listing_id,
            "item_type": "crop",
            "item_name": listing["crop_type"],
            "variety": listing.get("crop_variety"),
            "price_per_unit": listing["price_per_unit"],
            "quantity": listing["estimated_quantity"],
            "total_value": listing["price_per_unit"] * listing["estimated_quantity"],
            "quality_grade": listing.get("quality_grade"),
            "state": listing["location_state"],
            "district": listing["location_district"],
            "transaction_date": datetime.now(),
            "source": "marketplace",
        }

        # Determine season based on expected harvest date
        harvest_date = listing.get("expected_harvest_date")
        if harvest_date:
            price_data["season"] = self._determine_season(harvest_date)

        market_price = await _create_price(price_data)
        return market_price

    async def collect_price_from_booking(self, booking_id: int) -> Optional[Dict[str, Any]]:
        """
        Collect price data from an advance booking

        Args:
            booking_id: ID of the advance booking

        Returns:
            Created market price record or None
        """
        # Get booking details
        booking = await _find("advance_bookings", booking_id)
        if not booking:
            return None

        # Get associated listing for crop details
        listing = await _find("marketplace_listings", booking["listing_id"])
        if not listing:
            return None

        # Calculate quality premium if applicable
        quality_premium_percent = None
        if booking.get("price_per_unit") and listing.get("price_per_unit"):
            base_price = listing["price_per_unit"]
            booking_price = booking["price_per_unit"]
            if base_price > 0:
                quality_premium_percent = ((booking_price - base_price) / base_price) * 100

        # Create market price record
        price_data = {
            "booking_id": booking_id,
            "listing_id": booking["listing_id"],
            "item_type": "crop",
            "item_name": listing["crop_type"],
            "variety": listing.get("crop_variety"),
            "price_per_unit": booking["price_per_unit"],
            "quantity": booking["quantity_booked"],
            "total_value": booking["total_amount"],
            "quality_grade": listing.get("quality_grade"),
            "quality_premium_percent": quality_premium_percent,
            "state": listing["location_state"],
            "district": listing["location_district"],
            "transaction_date": booking.get("booking_date", datetime.now()),
            "source": "booking",
        }

        # Determine season
        delivery_date = booking.get("expected_delivery_date")
        if delivery_date:
            price_data["season"] = self._determine_season(delivery_date)

        market_price = await _create_price(price_data)
        return market_price

    async def collect_price_from_livestock_transaction(
        self, transaction_id: int
    ) -> Optional[Dict[str, Any]]:
        """
        Collect price data from a livestock transaction

        Args:
            transaction_id: ID of the livestock transaction

        Returns:
            Created market price record or None
        """
        # Get transaction details
        transaction = await _find("livestock_transactions", transaction_id)
        if not transaction or transaction["status"] not in ["agreed", "completed"]:
            return None

        # Get listing details
        from app.orm.livestock_listing import LivestockListing

        listing = await _find("livestock_listings", transaction["listing_id"])
        if not listing:
            return None

        # Create market price record
        price_data = {
            "transaction_id": transaction_id,
            "item_type": "livestock",
            "item_name": listing["species"],
            "variety": listing.get("breed"),
            "price_per_unit": transaction["agreed_price"] / transaction.get("quantity", 1),
            "quantity": transaction.get("quantity", 1),
            "total_value": transaction["agreed_price"],
            "state": listing["location_state"],
            "district": listing["location_district"],
            "transaction_date": transaction.get("completed_at") or datetime.now(),
            "source": "livestock_transaction",
        }

        market_price = await _create_price(price_data)
        return market_price

    async def get_price_trends(
        self,
        item_type: str,
        item_name: str,
        state: Optional[str] = None,
        district: Optional[str] = None,
        days: int = 90,
    ) -> Dict[str, Any]:
        """
        Get price trends for an item over time

        Args:
            item_type: Type of item (crop, livestock)
            item_name: Name of the item
            state: Optional state filter
            district: Optional district filter
            days: Number of days to look back

        Returns:
            Price trend analysis
        """
        cutoff_date = datetime.now() - timedelta(days=days)

        # Get all prices and filter
        all_prices = await _all_prices()

        prices = []
        for p in all_prices:
            if p["item_type"] != item_type or str(p["item_name"]).lower() != item_name.lower():
                continue
            if p["transaction_date"] < cutoff_date:
                continue
            if state and p["state"] != state:
                continue
            if district and p["district"] != district:
                continue
            prices.append(p)

        if not prices:
            return {
                "item_type": item_type,
                "item_name": item_name,
                "state": state,
                "district": district,
                "period_days": days,
                "data_points": 0,
                "trend": "insufficient_data",
            }

        # Calculate statistics
        price_values = [p["price_per_unit"] for p in prices]
        quantities = [p["quantity"] for p in prices]

        avg_price = sum(price_values) / len(price_values)
        min_price = min(price_values)
        max_price = max(price_values)
        total_volume = sum(quantities)

        # Calculate trend
        mid_point = len(prices) // 2
        if mid_point > 0:
            older_avg = sum(price_values[:mid_point]) / mid_point
            recent_avg = sum(price_values[mid_point:]) / (len(price_values) - mid_point)

            if recent_avg > older_avg * 1.05:
                trend = "up"
            elif recent_avg < older_avg * 0.95:
                trend = "down"
            else:
                trend = "stable"
        else:
            trend = "stable"

        # Group by month for time series
        monthly_data = {}
        for price in prices:
            month_key = price["transaction_date"].strftime("%Y-%m")
            if month_key not in monthly_data:
                monthly_data[month_key] = {"prices": [], "volumes": []}
            monthly_data[month_key]["prices"].append(price["price_per_unit"])
            monthly_data[month_key]["volumes"].append(price["quantity"])

        time_series = []
        for month, data in sorted(monthly_data.items()):
            time_series.append(
                {
                    "month": month,
                    "avg_price": sum(data["prices"]) / len(data["prices"]),
                    "total_volume": sum(data["volumes"]),
                    "transactions": len(data["prices"]),
                }
            )

        return {
            "item_type": item_type,
            "item_name": item_name,
            "state": state,
            "district": district,
            "period_days": days,
            "data_points": len(prices),
            "avg_price": round(avg_price, 2),
            "min_price": round(min_price, 2),
            "max_price": round(max_price, 2),
            "total_volume": round(total_volume, 2),
            "trend": trend,
            "time_series": time_series,
        }

    async def get_quality_premiums(
        self, item_type: str, item_name: str, state: Optional[str] = None, days: int = 90
    ) -> Dict[str, Any]:
        """
        Get quality premium analysis

        Args:
            item_type: Type of item (crop, livestock)
            item_name: Name of the item
            state: Optional state filter
            days: Number of days to look back

        Returns:
            Quality premium analysis by grade
        """
        cutoff_date = datetime.now() - timedelta(days=days)

        # Get all prices and filter
        all_prices = await _all_prices()

        prices = []
        for p in all_prices:
            if p["item_type"] != item_type or str(p["item_name"]).lower() != item_name.lower():
                continue
            if p["transaction_date"] < cutoff_date:
                continue
            if not p.get("quality_grade"):
                continue
            if state and p["state"] != state:
                continue
            prices.append(p)

        if not prices:
            return {
                "item_type": item_type,
                "item_name": item_name,
                "state": state,
                "data_points": 0,
                "grades": {},
            }

        # Group by quality grade
        grade_data = {}
        for price in prices:
            grade = price["quality_grade"]
            if grade not in grade_data:
                grade_data[grade] = {"prices": [], "premiums": []}
            grade_data[grade]["prices"].append(price["price_per_unit"])
            if price.get("quality_premium_percent"):
                grade_data[grade]["premiums"].append(price["quality_premium_percent"])

        # Calculate statistics per grade
        grades = {}
        for grade, data in grade_data.items():
            avg_price = sum(data["prices"]) / len(data["prices"])
            avg_premium = sum(data["premiums"]) / len(data["premiums"]) if data["premiums"] else 0

            grades[grade] = {
                "avg_price": round(avg_price, 2),
                "avg_premium_percent": round(avg_premium, 2),
                "transactions": len(data["prices"]),
            }

        return {
            "item_type": item_type,
            "item_name": item_name,
            "state": state,
            "period_days": days,
            "data_points": len(prices),
            "grades": grades,
        }

    async def get_demand_forecast(
        self, item_type: str, item_name: str, state: Optional[str] = None, days_ahead: int = 30
    ) -> Dict[str, Any]:
        """
        Forecast demand based on booking patterns

        Args:
            item_type: Type of item (crop, livestock)
            item_name: Name of the item
            state: Optional state filter
            days_ahead: Number of days to forecast

        Returns:
            Demand forecast
        """
        # Get historical booking data
        cutoff_date = datetime.now() - timedelta(days=90)

        # Get all prices and filter for bookings
        all_prices = await _all_prices()

        bookings = []
        for p in all_prices:
            if p["item_type"] != item_type or str(p["item_name"]).lower() != item_name.lower():
                continue
            if p["transaction_date"] < cutoff_date:
                continue
            if p["source"] != "booking":
                continue
            if state and p["state"] != state:
                continue
            bookings.append(p)

        if not bookings:
            return {
                "item_type": item_type,
                "item_name": item_name,
                "state": state,
                "forecast_days": days_ahead,
                "demand_level": "unknown",
                "confidence": 0.0,
            }

        # Calculate average booking volume
        total_volume = sum(b["quantity"] for b in bookings)
        avg_daily_volume = total_volume / 90

        # Simple forecast: project based on recent trend
        recent_bookings = [
            b for b in bookings if b["transaction_date"] >= datetime.now() - timedelta(days=30)
        ]
        if recent_bookings:
            recent_volume = sum(b["quantity"] for b in recent_bookings)
            recent_daily_avg = recent_volume / 30

            # Compare recent to overall average
            if recent_daily_avg > avg_daily_volume * 1.2:
                demand_level = "high"
                confidence = 0.75
            elif recent_daily_avg < avg_daily_volume * 0.8:
                demand_level = "low"
                confidence = 0.70
            else:
                demand_level = "medium"
                confidence = 0.80
        else:
            demand_level = "medium"
            confidence = 0.50

        forecasted_volume = avg_daily_volume * days_ahead

        return {
            "item_type": item_type,
            "item_name": item_name,
            "state": state,
            "forecast_days": days_ahead,
            "demand_level": demand_level,
            "forecasted_volume": round(forecasted_volume, 2),
            "confidence": confidence,
            "historical_daily_avg": round(avg_daily_volume, 2),
            "data_points": len(bookings),
        }

    def _determine_season(self, date: datetime) -> str:
        """Determine agricultural season from date"""
        month = date.month

        # Kharif: June-October (monsoon)
        if 6 <= month <= 10:
            return "Kharif"
        # Rabi: November-March (winter)
        elif month >= 11 or month <= 3:
            return "Rabi"
        # Zaid: April-May (summer)
        else:
            return "Zaid"
