"""
Marketplace Service for automatic listing creation and management
"""

import logging
import uuid
from datetime import date, datetime, timedelta
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from app.orm.buyer_interest import BuyerInterest
from app.orm.crop import Crop
from app.orm.farm import Farm
from app.orm.farm_plot import FarmPlot
from app.orm.marketplace_listing import MarketplaceListing
from app.orm.user import User
from app.services.bedrock_service import bedrock_service

logger = logging.getLogger(__name__)


class MarketplaceService:
    """
    Service for managing marketplace listings and buyer-farmer connections

    Validates: AC4.1, AC4.2, AC4.3, AC4.4, AC4.5
    """

    def __init__(self, db: Session):
        self.db = db
        self.bedrock = bedrock_service

    def create_automatic_listing(
        self, crop_id: int, farmer_id: int, yield_prediction: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Automatically create a marketplace listing for a farmer's crop (idempotent per crop)

        Validates: AC4.1 - Automatic listing when farmer confirms crop selection
        Validates: AC4.2 - Include all required fields
        """
        from app.core.db import DB

        rows = DB.raw(
            """SELECT c.*, f.id AS farm_id, f.location_state, f.location_district, f.location_village,
                      f.user_id AS farm_user_id, f.owner_id AS farm_owner_id
               FROM crops c JOIN farm_plots p ON p.id = c.farm_plot_id JOIN farms f ON f.id = p.farm_id
               WHERE c.id = ?""",
            [crop_id],
        ).result
        if not rows:
            raise ValueError("Crop not found")
        crop = rows[0]
        if farmer_id not in (crop["farm_user_id"], crop["farm_owner_id"]):
            raise ValueError("Crop not found")

        existing = DB.raw(
            """SELECT * FROM marketplace_listings WHERE farm_id = ? AND farmer_id = ? AND crop_type = ?
               AND expected_harvest_date = ? AND status = 'active'""",
            [crop["farm_id"], farmer_id, crop["crop_name"], crop["expected_harvest_date"]],
        ).result
        if existing:
            logger.info(f"Listing already exists for crop {crop_id}")
            return existing[0]

        farmer = DB.raw("SELECT phone, email FROM users WHERE id = ?", [farmer_id]).result
        farmer = farmer[0] if farmer else {}
        quantity = (
            (yield_prediction or {}).get("estimated_yield") or crop.get("expected_yield") or 0
        )
        listing = DB.raw(
            """INSERT INTO marketplace_listings
               (farm_id, farmer_id, crop_type, crop_variety, expected_harvest_date, estimated_quantity,
                available_quantity, quality_grade, location_state, location_district, delivery_village,
                farmer_contact_phone, farmer_contact_email, status)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'active') RETURNING *""",
            [
                crop["farm_id"],
                farmer_id,
                crop["crop_name"],
                crop.get("crop_variety"),
                crop["expected_harvest_date"],
                int(float(quantity)),
                int(float(quantity)),
                (yield_prediction or {}).get("quality_grade"),
                crop["location_state"],
                crop["location_district"],
                crop.get("location_village"),
                farmer.get("phone"),
                farmer.get("email"),
            ],
        ).result[0]
        logger.info(f"Created marketplace listing {listing['id']} for crop {crop_id}")
        return listing

    def _generate_yield_prediction(self, crop: Crop, plot: FarmPlot, farm: Farm) -> Dict[str, Any]:
        """Generate yield prediction using Bedrock"""
        try:
            crop_variety = crop.crop_variety
            crop_type = crop_variety.crop_type if crop_variety else "Unknown"
            variety_name = crop_variety.variety_name if crop_variety else "Standard"

            prediction = self.bedrock.predict_yield_and_harvest(
                crop_name=crop_type,
                variety=variety_name,
                state=farm.location_state,
                district=farm.location_district,
                planting_date=crop.planting_date.isoformat(),
                area_acres=float(crop.area_planted),
                soil_type=plot.soil_type,
                irrigation_type=plot.irrigation_type,
            )

            return prediction if prediction else self._get_fallback_prediction(crop)

        except Exception as e:
            logger.warning(f"Error generating yield prediction: {e}")
            return self._get_fallback_prediction(crop)

    def _get_fallback_prediction(self, crop: Crop) -> Dict[str, Any]:
        """Fallback prediction if Bedrock fails"""
        harvest_date = crop.expected_harvest_date or (crop.planting_date + timedelta(days=120))
        expected_yield = float(crop.area_planted) * 20  # Conservative 20 quintals/acre

        return {
            "harvest_date": harvest_date.isoformat(),
            "total_expected_yield": expected_yield,
            "quality_grade": "B",
            "confidence_score": 0.75,
        }

    def _get_market_intelligence(self, crop_type: str, state: str, district: str) -> Dict[str, Any]:
        """Get market intelligence for pricing"""
        # Simplified market data for MVP
        # In production, this would query the market_intelligence tables

        base_prices = {
            "rice": 2000,
            "wheat": 2100,
            "maize": 1800,
            "cotton": 5500,
            "soybean": 4000,
            "groundnut": 5000,
            "chickpea": 5500,
            "pigeon pea": 6000,
        }

        crop_lower = crop_type.lower()
        price = base_prices.get(crop_lower, 2500)

        return {
            "price_per_quintal": price,
            "demand_score": 0.75,
            "price_trend": "stable",
            "yoy_growth": 5.0,
        }

    def _generate_listing_description(
        self,
        crop_type: str,
        variety: str,
        area: float,
        expected_yield: float,
        quality_grade: str,
        harvest_date: date,
        farm_name: str,
    ) -> str:
        """Generate listing description"""
        return f"""High-quality {crop_type} ({variety}) available for advance booking.

Farm: {farm_name}
Cultivated Area: {area:.2f} acres
Expected Yield: {expected_yield:.2f} quintals
Quality Grade: {quality_grade}
Expected Harvest: {harvest_date.strftime('%B %Y')}

This crop is being grown using modern agricultural practices with AI-powered crop management. 
Advance booking available with flexible payment terms.

Contact farmer directly for inquiries and negotiations."""

    def register_buyer_interest(
        self, listing_id: int, buyer_id: int, interest_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Register buyer interest in a listing (one open interest per buyer and listing)

        Validates: AC4.3 - Buyers can express interest in advance booking
        """
        from app.core.db import DB

        listing = DB.raw(
            "SELECT id, farmer_id, status FROM marketplace_listings WHERE id = ?", [listing_id]
        ).result
        if not listing:
            raise ValueError("Listing not found")
        buyer = DB.raw(
            "SELECT id, name, phone, email, user_type FROM users WHERE id = ?", [buyer_id]
        ).result
        if not buyer:
            raise ValueError("Buyer not found")
        buyer = buyer[0]
        if listing[0]["farmer_id"] == buyer_id:
            raise ValueError("You cannot register interest in your own listing")

        phone = interest_data.get("buyer_phone") or buyer.get("phone") or ""
        existing = DB.raw(
            "SELECT * FROM buyer_interests WHERE listing_id = ? AND buyer_phone = ? AND status = 'pending'",
            [listing_id, phone],
        ).result
        if existing:
            logger.info(f"Buyer interest already exists for listing {listing_id}")
            return existing[0]

        message_parts = [interest_data.get("message")]
        for label, key in (
            ("Company", "buyer_company"),
            ("Quality", "quality_requirements"),
            ("Delivery", "delivery_requirements"),
            ("Payment", "payment_terms"),
            ("Preferred price", "preferred_price"),
        ):
            if interest_data.get(key) not in (None, ""):
                message_parts.append(f"{label}: {interest_data[key]}")
        message = "\n".join(str(m) for m in message_parts if m) or None

        rows = DB.raw(
            """INSERT INTO buyer_interests
               (listing_id, buyer_name, buyer_phone, buyer_email, buyer_type, interested_quantity, message, status)
               VALUES (?, ?, ?, ?, ?, ?, ?, 'pending') RETURNING *""",
            [
                listing_id,
                buyer.get("name") or "Buyer",
                phone,
                interest_data.get("buyer_email") or buyer.get("email"),
                interest_data.get("interest_type") or buyer.get("user_type") or "buyer",
                int(interest_data.get("quantity_interested") or 0),
                message,
            ],
        ).result
        logger.info(f"Registered buyer interest {rows[0]['id']} for listing {listing_id}")
        return rows[0]

    def get_listings(
        self,
        filters: Optional[Dict[str, Any]] = None,
        sort_by: str = "harvest_date",
        sort_order: str = "asc",
        limit: int = 20,
        offset: int = 0,
    ) -> tuple[List[Dict], int]:
        """
        Get marketplace listings with filters, sorting, and pagination

        Args:
            filters: Dictionary of filter criteria
            sort_by: Field to sort by (harvest_date, quantity, quality_grade)
            sort_order: Sort order (asc, desc)
            limit: Maximum number of results (default 20)
            offset: Number of results to skip (default 0)

        Returns:
            Tuple of (listings, total_count)

        Validates: AC4 - Marketplace search with filters, pagination, and sorting
        """
        try:
            # Base query - only active listings using custom ORM
            query = MarketplaceListing.where({"status": ["active"]})

            # Build count query with same filters
            count_query = MarketplaceListing.where({"status": ["active"]})

            # Apply filters
            if filters:
                # Crop type filter - use ILIKE for case-insensitive partial match
                if filters.get("crop_type"):
                    crop_type = filters["crop_type"].strip()
                    query = query.and_where_custom([["crop_type", "ILIKE", f"%{crop_type}%"]])
                    count_query = count_query.and_where_custom(
                        [["crop_type", "ILIKE", f"%{crop_type}%"]]
                    )

                # State filter - exact match
                if filters.get("state"):
                    query = query.and_where({"location_state": [filters["state"]]})
                    count_query = count_query.and_where({"location_state": [filters["state"]]})

                # District filter - exact match
                if filters.get("district"):
                    query = query.and_where({"location_district": [filters["district"]]})
                    count_query = count_query.and_where(
                        {"location_district": [filters["district"]]}
                    )

                # Quantity filters - range comparisons
                if filters.get("min_quantity"):
                    query = query.and_where_custom(
                        [["estimated_quantity", ">=", filters["min_quantity"]]]
                    )
                    count_query = count_query.and_where_custom(
                        [["estimated_quantity", ">=", filters["min_quantity"]]]
                    )

                if filters.get("max_quantity"):
                    query = query.and_where_custom(
                        [["estimated_quantity", "<=", filters["max_quantity"]]]
                    )
                    count_query = count_query.and_where_custom(
                        [["estimated_quantity", "<=", filters["max_quantity"]]]
                    )

                # Harvest date range filters
                if filters.get("harvest_from"):
                    query = query.and_where_custom(
                        [["expected_harvest_date", ">=", filters["harvest_from"]]]
                    )
                    count_query = count_query.and_where_custom(
                        [["expected_harvest_date", ">=", filters["harvest_from"]]]
                    )

                if filters.get("harvest_to"):
                    query = query.and_where_custom(
                        [["expected_harvest_date", "<=", filters["harvest_to"]]]
                    )
                    count_query = count_query.and_where_custom(
                        [["expected_harvest_date", "<=", filters["harvest_to"]]]
                    )

                # Quality grade filter - exact match
                if filters.get("quality_grade"):
                    query = query.and_where({"quality_grade": [filters["quality_grade"]]})
                    count_query = count_query.and_where(
                        {"quality_grade": [filters["quality_grade"]]}
                    )

                # Price range filters
                if filters.get("min_price"):
                    query = query.and_where_custom(
                        [["asking_price_per_unit", ">=", filters["min_price"]]]
                    )
                    count_query = count_query.and_where_custom(
                        [["asking_price_per_unit", ">=", filters["min_price"]]]
                    )

                if filters.get("max_price"):
                    query = query.and_where_custom(
                        [["asking_price_per_unit", "<=", filters["max_price"]]]
                    )
                    count_query = count_query.and_where_custom(
                        [["asking_price_per_unit", "<=", filters["max_price"]]]
                    )

            # Get total count before pagination
            count_result = count_query.count()
            total_count = count_result[0]["count"] if count_result else 0

            # Apply sorting using raw SQL ORDER BY
            sort_column_name = "expected_harvest_date"  # default

            if sort_by == "quantity":
                sort_column_name = "estimated_quantity"
            elif sort_by == "quality_grade":
                sort_column_name = "quality_grade"
            elif sort_by == "price":
                sort_column_name = "asking_price_per_unit"
            elif sort_by == "harvest_date":
                sort_column_name = "expected_harvest_date"

            # Use raw SQL for ORDER BY clause
            query.db.rawsql(f' ORDER BY "{sort_column_name}" {sort_order.upper()} ')

            # Apply pagination
            query.db.limit_q(limit).offset_q(offset)

            # Execute query and get results
            query.get()
            listings = query.items

            logger.info(f"Retrieved {len(listings)} listings (total: {total_count})")

            return listings, total_count

        except Exception as e:
            logger.error(f"Error getting listings: {e}")
            raise

    def get_listing_detail(self, listing_id: int) -> Optional[Dict[str, Any]]:
        """
        Get detailed listing information with production predictions and market intelligence

        Validates: AC4 - Listing detail view with comprehensive information
        """
        from app.core.db import DB

        rows = DB.raw("SELECT * FROM marketplace_listings WHERE id = ?", [listing_id]).result
        if not rows:
            return None
        listing = rows[0]
        interest_count = DB.raw(
            "SELECT COUNT(*) AS n FROM buyer_interests WHERE listing_id = ?", [listing_id]
        ).result[0]["n"]

        def num(v):
            return float(v) if v is not None else None

        harvest = listing["expected_harvest_date"]
        harvest_iso = harvest.isoformat() if hasattr(harvest, "isoformat") else harvest
        market_data = self._get_market_intelligence_detail(
            listing["crop_type"], listing["location_state"], listing["location_district"]
        )
        title = f"{listing['crop_type']}" + (
            f" ({listing['crop_variety']})" if listing.get("crop_variety") else ""
        )

        return {
            "id": str(listing["id"]),
            "title": title,
            "description": f"{title} from {listing['location_district']}, {listing['location_state']}",
            "crop_type": listing["crop_type"],
            "crop_variety": listing.get("crop_variety"),
            "estimated_quantity": num(listing["estimated_quantity"]),
            "available_quantity": num(listing.get("available_quantity")),
            "quantity_unit": "kg",
            "quality_grade": listing.get("quality_grade"),
            "expected_harvest_date": harvest_iso,
            "harvest_window": {"start": None, "end": None},
            "asking_price_per_unit": num(listing.get("price_per_unit")),
            "price_negotiable": True,
            "pricing": {
                "asking_price_per_unit": num(listing.get("price_per_unit")),
                "price_negotiable": True,
                "currency": "INR",
            },
            "location": {
                "state": listing["location_state"],
                "district": listing["location_district"],
                "village": listing.get("delivery_village"),
            },
            "location_state": listing["location_state"],
            "location_district": listing["location_district"],
            "contact": {
                "enabled": bool(
                    listing.get("farmer_contact_phone") or listing.get("farmer_contact_email")
                ),
                "phone": listing.get("farmer_contact_phone"),
                "email": listing.get("farmer_contact_email"),
            },
            "production_predictions": {
                "estimated_yield": {"quantity": num(listing["estimated_quantity"]), "unit": "kg"},
                "quality_prediction": {"grade": listing.get("quality_grade")},
                "harvest_timing": {"expected_date": harvest_iso},
            },
            "market_intelligence": market_data,
            "interest_registration": {
                "allowed": listing.get("status") == "active",
                "endpoint": "/marketplace/buyer-interest",
                "listing_id": str(listing["id"]),
            },
            "status": listing.get("status"),
            "farmer_id": listing["farmer_id"],
            "view_count": 0,
            "interest_count": interest_count,
            "listed_at": listing["created_at"].isoformat() if listing.get("created_at") else None,
            "images": [],
            "videos": [],
        }

    def _get_market_intelligence_detail(
        self, crop_type: str, state: str, district: str
    ) -> Dict[str, Any]:
        """Recent prices for this crop from crop_market_data (state and district level)."""
        from app.core.db import DB

        rows = (
            DB.raw(
                """SELECT district, price_per_kg, date, yoy_growth, demand_level FROM crop_market_data
               WHERE crop_name ILIKE ? AND state = ? ORDER BY date DESC LIMIT 12""",
                [crop_type, state],
            ).result
            or []
        )
        if not rows:
            return {
                "data_available": False,
                "message": "No recent market data for this crop and state",
            }
        latest = next((r for r in rows if r.get("district") == district), rows[0])
        prices = [float(r["price_per_kg"]) for r in rows if r.get("price_per_kg") is not None]
        trend = "stable"
        if len(prices) >= 2 and prices[0] > prices[-1] * 1.02:
            trend = "rising"
        elif len(prices) >= 2 and prices[0] < prices[-1] * 0.98:
            trend = "falling"
        yoy = float(latest["yoy_growth"]) if latest.get("yoy_growth") is not None else None
        return {
            "data_available": True,
            "current_price_per_kg": float(latest["price_per_kg"]),
            "average_price_per_kg": round(sum(prices) / len(prices), 2) if prices else None,
            "price_trend": trend,
            "yoy_growth": yoy,
            "yoy_growth_description": self._get_yoy_growth_description(yoy),
            "demand_level": latest.get("demand_level"),
            "as_of": (
                latest["date"].isoformat()
                if hasattr(latest["date"], "isoformat")
                else latest["date"]
            ),
        }

    def _get_yoy_growth_description(self, yoy_growth: Optional[float]) -> str:
        """Get human-readable description of YoY growth"""
        if yoy_growth is None:
            return "Historical data not available"

        if yoy_growth > 15:
            return "Strong price growth - High demand"
        elif yoy_growth > 5:
            return "Moderate price growth - Increasing demand"
        elif yoy_growth > -5:
            return "Stable prices - Steady demand"
        elif yoy_growth > -15:
            return "Moderate price decline - Decreasing demand"
        else:
            return "Significant price decline - Low demand"

    def _get_seasonal_insights(
        self, crop_type: str, state: str, recent_data: List
    ) -> Optional[Dict[str, Any]]:
        """Get seasonal insights for the crop"""
        if not recent_data:
            return None

        try:
            # Group by season
            seasonal_prices = {}
            for data in recent_data:
                if data.season:
                    season = data.season.lower()
                    if season not in seasonal_prices:
                        seasonal_prices[season] = []
                    seasonal_prices[season].append(float(data.avg_price_per_quintal))

            # Calculate average by season
            seasonal_averages = {}
            for season, prices in seasonal_prices.items():
                seasonal_averages[season] = sum(prices) / len(prices)

            # Find best season
            best_season = None
            if seasonal_averages:
                best_season = max(seasonal_averages, key=seasonal_averages.get)

            return {
                "seasonal_prices": seasonal_averages,
                "best_season": best_season,
                "best_season_price": seasonal_averages.get(best_season) if best_season else None,
            }

        except Exception as e:
            logger.warning(f"Error getting seasonal insights: {e}")
            return None
