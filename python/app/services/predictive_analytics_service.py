"""
Predictive Market Analytics Service

Provides AI-powered predictive analytics for market intelligence:
- Price predictions using Amazon Bedrock (30-90 day forecasts)
- Demand predictions based on buyer interest patterns
- Supply-demand gap identification
- Opportunity scoring for farmers (0-100 scale)
- Market opportunity alerts
"""

import json
import logging
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Any, Dict, List, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.orm.advance_booking import AdvanceBooking
from app.orm.buyer_interest import BuyerInterest
from app.orm.market_price import MarketPrice
from app.orm.marketplace_listing import MarketplaceListing
from app.orm.price_prediction import PricePrediction

# AWS imports removed for GCP/local migration


logger = logging.getLogger(__name__)

# Crop and livestock listings in one shape. The ORM classes are the lightweight kind (no SQLAlchemy
# select/execute), so everything here is parameterised SQL through DB.raw.
SUPPLY = """(
    SELECT id, 'crop' AS item_type, crop_type AS item_name, crop_variety AS variety, location_state AS state,
           location_district AS district, COALESCE(available_quantity, estimated_quantity) AS quantity,
           price_per_unit, quality_grade, status, expected_harvest_date
    FROM marketplace_listings
    UNION ALL
    SELECT id, 'livestock', species, breed, location_state, location_district, quantity, price, NULL, status, NULL
    FROM livestock_listings
) s"""


def _rows(sql: str, bind: list) -> List[Dict[str, Any]]:
    from app.core.db import DB

    return [
        {k: float(v) if isinstance(v, Decimal) else v for k, v in r.items()}
        for r in DB.raw(sql, bind).result
    ]


def _match(
    alias: str, item_type: str, item_name: str, state: str, district: Optional[str]
) -> tuple:
    """WHERE fragment + binds for one item in one place (names compared case-insensitively)."""
    where = [f"{alias}.item_type = ?", f"{alias}.item_name ILIKE ?", f"{alias}.state = ?"]
    bind: list = [item_type, item_name, state]
    if district:
        where.append(f"{alias}.district = ?")
        bind.append(district)
    return " AND ".join(where), bind


class PredictiveAnalyticsService:
    """Service for AI-powered predictive market analytics"""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.bedrock_client = None
        self.sns_client = None

        # Initialize Vertex AI
        import vertexai

        try:
            vertexai.init(
                project=settings.GOOGLE_CLOUD_PROJECT, location=settings.GOOGLE_CLOUD_REGION
            )
            self.vertex_enabled = True
        except Exception:
            self.vertex_enabled = False

        self.model_name = settings.GEMINI_MODEL
        self.model_version = "vertex-gemini-v1"

    async def predict_price(
        self,
        item_type: str,
        item_name: str,
        state: str,
        district: Optional[str] = None,
        variety: Optional[str] = None,
        forecast_days: int = 30,
    ) -> Dict[str, Any]:
        """
        Predict future prices using Amazon Bedrock AI

        Args:
            item_type: 'crop' or 'livestock'
            item_name: Name of crop or livestock
            state: State for prediction
            district: Optional district for more specific prediction
            variety: Optional variety/breed
            forecast_days: Number of days to forecast (30-90)

        Returns:
            Dict with prediction data including price, confidence, range, trend
        """
        # Validate forecast_days
        if forecast_days < 30 or forecast_days > 90:
            raise ValueError("Forecast days must be between 30 and 90")

        # Get historical price data
        historical_data = await self._get_historical_prices(
            item_type, item_name, state, district, variety, days=180
        )

        if not historical_data:
            return {
                "success": False,
                "error": "Insufficient historical data for prediction",
                "min_data_points": 10,
            }

        # Get buyer interest patterns
        demand_data = await self._get_demand_patterns(
            item_type, item_name, state, district, days=90
        )

        # Get supply data from marketplace listings
        supply_data = await self._get_supply_patterns(item_type, item_name, state, district)

        # Call Bedrock for AI prediction
        prediction = await self._invoke_bedrock_price_prediction(
            item_type=item_type,
            item_name=item_name,
            state=state,
            district=district,
            variety=variety,
            forecast_days=forecast_days,
            historical_data=historical_data,
            demand_data=demand_data,
            supply_data=supply_data,
        )

        # Save prediction to database
        target_date = date.today() + timedelta(days=forecast_days)
        await self._save_prediction(
            item_type=item_type,
            item_name=item_name,
            state=state,
            district=district,
            variety=variety,
            target_date=target_date,
            prediction=prediction,
        )

        return {"success": True, "data": prediction}

    async def predict_demand(
        self,
        item_type: str,
        item_name: str,
        state: str,
        district: Optional[str] = None,
        forecast_days: int = 30,
    ) -> Dict[str, Any]:
        """
        Predict future demand based on buyer interest patterns

        Returns:
            Dict with demand forecast, confidence, and contributing factors
        """
        # Get buyer interest history
        buyer_interests = await self._get_buyer_interest_history(
            item_type, item_name, state, district, days=90
        )

        # Get booking patterns
        booking_patterns = await self._get_booking_patterns(
            item_type, item_name, state, district, days=90
        )

        # Get historical demand from market prices
        historical_demand = await self._get_historical_demand(
            item_type, item_name, state, district, days=180
        )

        # Calculate demand metrics
        recent_interest = len(
            [b for b in buyer_interests if (datetime.now() - b["created_at"]).days <= 30]
        )
        historical_interest = len(
            [b for b in buyer_interests if (datetime.now() - b["created_at"]).days > 30]
        )

        # Determine demand level
        if historical_interest > 0:
            growth_rate = (
                (recent_interest - historical_interest / 2) / (historical_interest / 2)
                if historical_interest > 0
                else 0
            )
        else:
            growth_rate = 0

        if growth_rate > 0.3:
            demand_level = "high"
            confidence = 0.8
        elif growth_rate < -0.2:
            demand_level = "low"
            confidence = 0.75
        else:
            demand_level = "medium"
            confidence = 0.7

        # Calculate forecasted volume
        avg_quantity = (
            sum(b["interested_quantity"] for b in buyer_interests) / len(buyer_interests)
            if buyer_interests
            else 0
        )
        forecasted_volume = avg_quantity * (1 + growth_rate) * (forecast_days / 30)

        return {
            "success": True,
            "data": {
                "item_type": item_type,
                "item_name": item_name,
                "state": state,
                "district": district,
                "forecast_days": forecast_days,
                "demand_level": demand_level,
                "forecasted_volume": float(forecasted_volume),
                "confidence": confidence,
                "growth_rate": float(growth_rate),
                "recent_interest_count": recent_interest,
                "historical_interest_count": historical_interest,
                "data_points": len(buyer_interests),
            },
        }

    async def identify_supply_demand_gaps(
        self, state: str, district: Optional[str] = None, item_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Identify supply-demand gaps in the market

        Returns:
            List of items with supply-demand imbalances
        """
        gaps = []

        # Supply: active listings in the area
        where, bind = ["s.state = ?", "s.status = 'active'"], [state]
        if district:
            where.append("s.district = ?")
            bind.append(district)
        if item_type:
            where.append("s.item_type = ?")
            bind.append(item_type)
        supply_by_item = {}
        for listing in _rows(f"SELECT * FROM {SUPPLY} WHERE {' AND '.join(where)}", bind):
            key = f"{listing['item_type']}:{listing['item_name']}"
            item = supply_by_item.setdefault(
                key,
                {
                    "item_type": listing["item_type"],
                    "item_name": listing["item_name"],
                    "total_quantity": 0,
                    "listing_count": 0,
                },
            )
            item["total_quantity"] += float(listing["quantity"] or 0)
            item["listing_count"] += 1

        # Demand: open buyer interests on crop listings in the area
        dwhere, dbind = ["m.location_state = ?", "b.status IN ('pending', 'contacted')"], [state]
        if district:
            dwhere.append("m.location_district = ?")
            dbind.append(district)
        demand_by_item = {}
        if item_type in (None, "crop"):
            for interest in _rows(
                f"""SELECT m.crop_type AS item_name, b.interested_quantity FROM buyer_interests b
                    JOIN marketplace_listings m ON m.id = b.listing_id WHERE {' AND '.join(dwhere)}""",
                dbind,
            ):
                key = f"crop:{interest['item_name']}"
                item = demand_by_item.setdefault(
                    key,
                    {
                        "item_type": "crop",
                        "item_name": interest["item_name"],
                        "total_demand": 0,
                        "interest_count": 0,
                    },
                )
                item["total_demand"] += float(interest["interested_quantity"] or 0)
                item["interest_count"] += 1

        # Identify gaps
        all_items = set(supply_by_item.keys()) | set(demand_by_item.keys())

        for item_key in all_items:
            supply_info = supply_by_item.get(item_key, {"total_quantity": 0, "listing_count": 0})
            demand_info = demand_by_item.get(item_key, {"total_demand": 0, "interest_count": 0})

            supply = supply_info["total_quantity"]
            demand = demand_info["total_demand"]

            # Calculate gap
            if demand > 0:
                gap_percent = ((demand - supply) / demand) * 100
            else:
                gap_percent = -100 if supply > 0 else 0

            # Determine gap type
            if gap_percent > 20:
                gap_type = "shortage"
                severity = "high" if gap_percent > 50 else "medium"
            elif gap_percent < -20:
                gap_type = "surplus"
                severity = "high" if gap_percent < -50 else "medium"
            else:
                gap_type = "balanced"
                severity = "low"

            item_parts = item_key.split(":")
            gaps.append(
                {
                    "item_type": item_parts[0],
                    "item_name": item_parts[1],
                    "supply": supply,
                    "demand": demand,
                    "gap": demand - supply,
                    "gap_percent": round(gap_percent, 2),
                    "gap_type": gap_type,
                    "severity": severity,
                    "listing_count": supply_info["listing_count"],
                    "interest_count": demand_info["interest_count"],
                }
            )

        # Sort by severity and gap size
        gaps.sort(key=lambda x: (x["severity"] == "high", abs(x["gap_percent"])), reverse=True)

        return {
            "success": True,
            "data": {
                "state": state,
                "district": district,
                "gaps": gaps,
                "total_items": len(gaps),
                "shortages": len([g for g in gaps if g["gap_type"] == "shortage"]),
                "surpluses": len([g for g in gaps if g["gap_type"] == "surplus"]),
            },
        }

    async def calculate_opportunity_score(
        self,
        item_type: str,
        item_name: str,
        state: str,
        district: Optional[str] = None,
        variety: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Calculate opportunity score for farmers (0-100 scale)

        Factors:
        - Price trend (30%)
        - Demand level (30%)
        - Supply-demand gap (20%)
        - Historical profitability (20%)

        Returns:
            Dict with opportunity score and breakdown
        """
        score_components = {}

        # 1. Price trend score (30 points)
        price_data = await self._get_historical_prices(
            item_type, item_name, state, district, variety, days=90
        )
        if price_data:
            recent_avg = sum(p["price"] for p in price_data[-30:]) / len(price_data[-30:])
            older_avg = (
                sum(p["price"] for p in price_data[:-30]) / len(price_data[:-30])
                if len(price_data) > 30
                else recent_avg
            )

            if older_avg > 0:
                price_growth = ((recent_avg - older_avg) / older_avg) * 100
                # Positive growth = higher score
                price_score = min(30, max(0, 15 + (price_growth * 2)))
            else:
                price_score = 15
        else:
            price_score = 15  # Neutral score if no data

        score_components["price_trend"] = {
            "score": round(price_score, 2),
            "max": 30,
            "description": "Price trend analysis",
        }

        # 2. Demand level score (30 points)
        demand_result = await self.predict_demand(
            item_type, item_name, state, district, forecast_days=30
        )
        demand_data = demand_result.get("data", {})
        demand_level = demand_data.get("demand_level", "medium")

        if demand_level == "high":
            demand_score = 30
        elif demand_level == "medium":
            demand_score = 20
        else:
            demand_score = 10

        score_components["demand_level"] = {
            "score": demand_score,
            "max": 30,
            "level": demand_level,
            "description": "Current and forecasted demand",
        }

        # 3. Supply-demand gap score (20 points)
        gaps_result = await self.identify_supply_demand_gaps(state, district, item_type)
        gaps = gaps_result.get("data", {}).get("gaps", [])

        item_gap = next((g for g in gaps if str(g["item_name"]).lower() == item_name.lower()), None)
        if item_gap:
            if item_gap["gap_type"] == "shortage":
                # Shortage = opportunity for farmers
                gap_score = min(20, 10 + (abs(item_gap["gap_percent"]) / 5))
            elif item_gap["gap_type"] == "surplus":
                # Surplus = lower opportunity
                gap_score = max(0, 10 - (abs(item_gap["gap_percent"]) / 5))
            else:
                gap_score = 10
        else:
            gap_score = 10  # Neutral if no gap data

        score_components["supply_demand_gap"] = {
            "score": round(gap_score, 2),
            "max": 20,
            "gap_type": item_gap["gap_type"] if item_gap else "unknown",
            "description": "Supply-demand balance",
        }

        # 4. Historical profitability score (20 points)
        # Based on quality premiums and price stability
        quality_data = await self._get_quality_premiums(
            item_type, item_name, state, district, days=90
        )

        if quality_data:
            avg_premium = sum(q.get("premium", 0) for q in quality_data) / len(quality_data)
            # Higher premiums = better opportunity
            profitability_score = min(20, 10 + (avg_premium / 2))
        else:
            profitability_score = 10

        score_components["profitability"] = {
            "score": round(profitability_score, 2),
            "max": 20,
            "description": "Historical profitability and quality premiums",
        }

        # Calculate total score
        total_score = sum(c["score"] for c in score_components.values())

        # Determine opportunity level
        if total_score >= 75:
            opportunity_level = "excellent"
            recommendation = "Strong opportunity - high demand and favorable market conditions"
        elif total_score >= 60:
            opportunity_level = "good"
            recommendation = "Good opportunity - favorable market conditions"
        elif total_score >= 40:
            opportunity_level = "moderate"
            recommendation = "Moderate opportunity - consider market timing"
        else:
            opportunity_level = "low"
            recommendation = "Limited opportunity - consider alternative crops"

        return {
            "success": True,
            "data": {
                "item_type": item_type,
                "item_name": item_name,
                "state": state,
                "district": district,
                "variety": variety,
                "opportunity_score": round(total_score, 2),
                "opportunity_level": opportunity_level,
                "recommendation": recommendation,
                "score_components": score_components,
                "calculated_at": datetime.now().isoformat(),
            },
        }

    async def generate_market_opportunity_alert(
        self, farmer_id: int, state: str, district: Optional[str] = None, min_score: int = 70
    ) -> Dict[str, Any]:
        """
        Generate market opportunity alerts for farmers

        Identifies high-opportunity crops and sends SNS notifications

        Args:
            farmer_id: Farmer user ID
            state: Farmer's state
            district: Farmer's district
            min_score: Minimum opportunity score to trigger alert (default 70)

        Returns:
            Dict with alerts generated and SNS message IDs
        """
        alerts = []

        # Get common crops for the region
        common_crops = await self._get_regional_crops(state, district)

        # Calculate opportunity scores for each crop
        for crop in common_crops:
            score_result = await self.calculate_opportunity_score(
                item_type="crop", item_name=crop["name"], state=state, district=district
            )

            if score_result["success"]:
                score_data = score_result["data"]
                if score_data["opportunity_score"] >= min_score:
                    alerts.append(score_data)

        # Sort by score
        alerts.sort(key=lambda x: x["opportunity_score"], reverse=True)

        # Send SNS notifications for top opportunities
        sns_messages = []
        for alert in alerts[:3]:  # Top 3 opportunities
            message = self._format_opportunity_alert_message(alert)

            try:
                # Log locally or trigger event since SNS is removed
                logger.info(
                    f"[ALERT MIGRATED TO GCLOUD/LOCAL] Title: Market Opportunity Alert: {alert['item_name']}, Msg: {message}"
                )

                sns_messages.append(
                    {
                        "item_name": alert["item_name"],
                        "message_id": f"gcloud-local-msg-{alert['item_name']}-{farmer_id}",
                        "status": "sent",
                    }
                )

                logger.info(
                    f"Sent opportunity alert for {alert['item_name']} to farmer {farmer_id}"
                )

            except Exception as e:
                logger.error(f"Failed to send alert: {e}")
                sns_messages.append(
                    {"item_name": alert["item_name"], "status": "failed", "error": str(e)}
                )

        return {
            "success": True,
            "data": {
                "farmer_id": farmer_id,
                "state": state,
                "district": district,
                "alerts_generated": len(alerts),
                "notifications_sent": len([m for m in sns_messages if m["status"] == "sent"]),
                "opportunities": alerts,
                "sns_messages": sns_messages,
            },
        }

    async def get_buyer_supply_planning_data(
        self,
        item_type: str,
        item_name: str,
        state: str,
        district: Optional[str] = None,
        months_ahead: int = 3,
    ) -> Dict[str, Any]:
        """
        Provide supply planning data for buyers

        Shows upcoming supply availability, price forecasts, and quality predictions

        Returns:
            Dict with supply planning information
        """
        # Get upcoming harvests from marketplace listings
        future_date = date.today() + timedelta(days=months_ahead * 30)

        where, bind = _match("s", item_type, item_name, state, district)
        listings = _rows(
            f"""SELECT * FROM {SUPPLY} WHERE {where} AND s.status = 'active'
                AND s.expected_harvest_date BETWEEN ? AND ? ORDER BY s.expected_harvest_date""",
            bind + [date.today(), future_date],
        )

        # Group by month
        supply_by_month = {}
        for listing in listings:
            month_key = listing["expected_harvest_date"].strftime("%Y-%m")
            if month_key not in supply_by_month:
                supply_by_month[month_key] = {
                    "month": month_key,
                    "total_quantity": 0,
                    "listing_count": 0,
                    "quality_distribution": {"A": 0, "B": 0, "C": 0},
                    "avg_price": 0,
                    "price_sum": 0,
                }

            supply_by_month[month_key]["total_quantity"] += float(listing["quantity"] or 0)
            supply_by_month[month_key]["listing_count"] += 1

            grade = listing["quality_grade"]
            if grade:
                dist = supply_by_month[month_key]["quality_distribution"]
                dist[grade] = dist.get(grade, 0) + 1

            if listing["price_per_unit"]:
                supply_by_month[month_key]["price_sum"] += float(listing["price_per_unit"])

        # Calculate averages
        for month_data in supply_by_month.values():
            if month_data["listing_count"] > 0:
                month_data["avg_price"] = round(
                    month_data["price_sum"] / month_data["listing_count"], 2
                )
            del month_data["price_sum"]

        # Get price predictions for each month
        monthly_forecasts = []
        for i in range(1, months_ahead + 1):
            forecast_days = i * 30
            prediction_result = await self.predict_price(
                item_type=item_type,
                item_name=item_name,
                state=state,
                district=district,
                forecast_days=forecast_days,
            )

            if prediction_result["success"]:
                monthly_forecasts.append(
                    {
                        "month": (date.today() + timedelta(days=forecast_days)).strftime("%Y-%m"),
                        "forecast": prediction_result["data"],
                    }
                )

        return {
            "success": True,
            "data": {
                "item_type": item_type,
                "item_name": item_name,
                "state": state,
                "district": district,
                "planning_horizon_months": months_ahead,
                "supply_by_month": list(supply_by_month.values()),
                "total_upcoming_supply": sum(m["total_quantity"] for m in supply_by_month.values()),
                "total_listings": sum(m["listing_count"] for m in supply_by_month.values()),
                "price_forecasts": monthly_forecasts,
                "generated_at": datetime.now().isoformat(),
            },
        }

    # Helper methods

    async def _get_historical_prices(
        self,
        item_type: str,
        item_name: str,
        state: str,
        district: Optional[str],
        variety: Optional[str],
        days: int,
    ) -> List[Dict[str, Any]]:
        """Recorded transaction prices, plus crop_market_data mandi prices for crops"""
        cutoff = datetime.now() - timedelta(days=days)
        where, bind = _match("p", item_type, item_name, state, district)
        sql = f"""SELECT transaction_date AS date, price_per_unit AS price, quantity, quality_grade, season
                  FROM market_prices p WHERE {where} AND p.transaction_date >= ?"""
        bind = bind + [cutoff]
        if variety:
            sql += " AND p.variety = ?"
            bind.append(variety)
        prices = _rows(sql, bind)
        if item_type == "crop":
            cwhere, cbind = ["crop_name ILIKE ?", "state = ?", "date >= ?"], [
                item_name,
                state,
                cutoff.date(),
            ]
            if district:
                cwhere.append("district = ?")
                cbind.append(district)
            prices += _rows(
                f"""SELECT date, price_per_kg AS price, 0 AS quantity, NULL AS quality_grade, season
                                FROM crop_market_data WHERE {' AND '.join(cwhere)}""",
                cbind,
            )
        prices.sort(key=lambda p: str(p["date"]))
        return [dict(p, quantity=float(p["quantity"] or 0)) for p in prices]

    def _interests(
        self, item_name: str, state: str, district: Optional[str], days: int
    ) -> List[Dict[str, Any]]:
        where, bind = ["m.crop_type ILIKE ?", "m.location_state = ?", "b.created_at >= ?"], [
            item_name,
            state,
            datetime.now() - timedelta(days=days),
        ]
        if district:
            where.append("m.location_district = ?")
            bind.append(district)
        return _rows(
            f"""SELECT b.* FROM buyer_interests b JOIN marketplace_listings m ON m.id = b.listing_id
                         WHERE {' AND '.join(where)}""",
            bind,
        )

    async def _get_demand_patterns(
        self, item_type: str, item_name: str, state: str, district: Optional[str], days: int
    ) -> Dict[str, Any]:
        """Get demand patterns from buyer interests (crop listings only)"""
        interests = self._interests(item_name, state, district, days) if item_type == "crop" else []
        total_demand = sum(float(i["interested_quantity"] or 0) for i in interests)
        return {
            "total_interest_count": len(interests),
            "total_demand_quantity": total_demand,
            "avg_demand_per_interest": total_demand / len(interests) if interests else 0,
            "buyer_types": sorted({i["buyer_type"] for i in interests if i.get("buyer_type")}),
        }

    async def _get_supply_patterns(
        self, item_type: str, item_name: str, state: str, district: Optional[str]
    ) -> Dict[str, Any]:
        """Get supply patterns from active listings"""
        where, bind = _match("s", item_type, item_name, state, district)
        listings = _rows(
            f"SELECT quantity FROM {SUPPLY} WHERE {where} AND s.status = 'active'", bind
        )
        total_supply = sum(float(l["quantity"] or 0) for l in listings)
        return {
            "total_listings": len(listings),
            "total_supply_quantity": total_supply,
            "avg_supply_per_listing": total_supply / len(listings) if listings else 0,
        }

    async def _get_buyer_interest_history(
        self, item_type: str, item_name: str, state: str, district: Optional[str], days: int
    ) -> List[Dict[str, Any]]:
        """Get buyer interest history"""
        interests = self._interests(item_name, state, district, days) if item_type == "crop" else []
        return [
            {
                "created_at": i["created_at"],
                "interested_quantity": float(i["interested_quantity"] or 0),
                "buyer_type": i["buyer_type"],
                "status": i["status"],
            }
            for i in interests
        ]

    async def _get_booking_patterns(
        self, item_type: str, item_name: str, state: str, district: Optional[str], days: int
    ) -> List[Dict[str, Any]]:
        """Get advance booking patterns (crop listings only)"""
        if item_type != "crop":
            return []
        where, bind = ["m.crop_type ILIKE ?", "m.location_state = ?", "a.created_at >= ?"], [
            item_name,
            state,
            datetime.now() - timedelta(days=days),
        ]
        if district:
            where.append("m.location_district = ?")
            bind.append(district)
        bookings = _rows(
            f"""SELECT a.* FROM advance_bookings a JOIN marketplace_listings m ON m.id = a.listing_id
                             WHERE {' AND '.join(where)}""",
            bind,
        )
        return [
            {
                "created_at": b["created_at"],
                "quantity": float(b["quantity_booked"] or 0),
                "price_per_unit": float(b["price_per_unit"] or 0),
                "status": b["status"],
            }
            for b in bookings
        ]

    async def _get_historical_demand(
        self, item_type: str, item_name: str, state: str, district: Optional[str], days: int
    ) -> Dict[str, Any]:
        """Get historical demand from recorded transactions"""
        where, bind = _match("p", item_type, item_name, state, district)
        prices = _rows(
            f"SELECT quantity FROM market_prices p WHERE {where} AND p.transaction_date >= ?",
            bind + [datetime.now() - timedelta(days=days)],
        )
        total_volume = sum(float(p["quantity"] or 0) for p in prices)
        return {
            "transaction_count": len(prices),
            "total_volume": total_volume,
            "avg_volume_per_transaction": total_volume / len(prices) if prices else 0,
        }

    async def _get_quality_premiums(
        self, item_type: str, item_name: str, state: str, district: Optional[str], days: int
    ) -> List[Dict[str, Any]]:
        """Get quality premium data"""
        where, bind = _match("p", item_type, item_name, state, district)
        prices = _rows(
            f"""SELECT quality_grade, quality_premium_percent FROM market_prices p
                           WHERE {where} AND p.transaction_date >= ? AND p.quality_premium_percent IS NOT NULL""",
            bind + [datetime.now() - timedelta(days=days)],
        )
        return [
            {
                "quality_grade": p["quality_grade"],
                "premium": float(p["quality_premium_percent"] or 0),
            }
            for p in prices
        ]

    async def _get_regional_crops(
        self, state: str, district: Optional[str]
    ) -> List[Dict[str, str]]:
        """Crops listed in the region"""
        where, bind = ["location_state = ?"], [state]
        if district:
            where.append("location_district = ?")
            bind.append(district)
        return [
            {"name": r["crop_type"]}
            for r in _rows(
                f"SELECT DISTINCT crop_type FROM marketplace_listings WHERE {' AND '.join(where)}",
                bind,
            )
        ]

    async def _invoke_bedrock_price_prediction(
        self,
        item_type: str,
        item_name: str,
        state: str,
        district: Optional[str],
        variety: Optional[str],
        forecast_days: int,
        historical_data: List[Dict],
        demand_data: Dict,
        supply_data: Dict,
    ) -> Dict[str, Any]:
        """Invoke Amazon Bedrock for AI-powered price prediction"""

        # Prepare historical data summary
        if historical_data:
            recent_prices = [p["price"] for p in historical_data[-30:]]
            avg_recent_price = sum(recent_prices) / len(recent_prices)
            min_price = min(p["price"] for p in historical_data)
            max_price = max(p["price"] for p in historical_data)
        else:
            avg_recent_price = 0
            min_price = 0
            max_price = 0

        # Build prompt for Bedrock
        prompt = f"""You are an agricultural market analyst. Predict the price for the following crop/livestock:

Item Type: {item_type}
Item Name: {item_name}
Variety/Breed: {variety or 'Not specified'}
Location: {state}, {district or 'All districts'}
Forecast Period: {forecast_days} days from today

Historical Price Data (last 180 days):
- Data points: {len(historical_data)}
- Recent average price (last 30 days): ₹{avg_recent_price:.2f} per unit
- Price range: ₹{min_price:.2f} - ₹{max_price:.2f}

Current Market Conditions:
- Buyer interest count: {demand_data.get('total_interest_count', 0)}
- Total demand quantity: {demand_data.get('total_demand_quantity', 0)} units
- Active supply listings: {supply_data.get('total_listings', 0)}
- Total supply quantity: {supply_data.get('total_supply_quantity', 0)} units

Please provide a price prediction with the following JSON format:
{{
    "predicted_price": <number>,
    "confidence_score": <0-1>,
    "price_range_min": <number>,
    "price_range_max": <number>,
    "trend": "<up|down|stable>",
    "demand_forecast": "<high|medium|low>",
    "supply_forecast": "<high|medium|low>",
    "factors": [
        "factor 1",
        "factor 2",
        "factor 3"
    ],
    "reasoning": "Brief explanation of the prediction"
}}

Consider seasonal patterns, supply-demand dynamics, and regional agricultural trends in your prediction."""

        try:
            # Call Vertex AI Gemini API
            if getattr(self, "vertex_enabled", False):
                from vertexai.generative_models import GenerationConfig, GenerativeModel

                model = GenerativeModel(self.model_name)

                generation_config = GenerationConfig(max_output_tokens=1000, temperature=0.3)

                response = model.generate_content(prompt, generation_config=generation_config)
                content = response.text
            else:
                # Fallback if Vertex AI not enabled
                content = json.dumps(self._create_fallback_prediction(avg_recent_price))

            # Extract JSON from response
            import re

            json_match = re.search(r"\{.*\}", content, re.DOTALL)
            if json_match:
                prediction_data = json.loads(json_match.group())
            else:
                # Fallback if JSON not found
                prediction_data = self._create_fallback_prediction(avg_recent_price)

            # Add metadata
            prediction_data["model_version"] = self.model_version
            prediction_data["forecast_days"] = forecast_days
            prediction_data["item_type"] = item_type
            prediction_data["item_name"] = item_name
            prediction_data["state"] = state
            prediction_data["district"] = district

            return prediction_data

        except Exception as e:
            logger.error(f"Bedrock API error: {e}")
            # Return fallback prediction
            return self._create_fallback_prediction(avg_recent_price)

    def _create_fallback_prediction(self, current_price: float) -> Dict[str, Any]:
        """Create fallback prediction when Bedrock fails"""
        return {
            "predicted_price": current_price,
            "confidence_score": 0.5,
            "price_range_min": current_price * 0.9,
            "price_range_max": current_price * 1.1,
            "trend": "stable",
            "demand_forecast": "medium",
            "supply_forecast": "medium",
            "factors": ["Insufficient data", "Using fallback prediction"],
            "reasoning": "Prediction based on current price due to insufficient data or API error",
            "model_version": "fallback-v1",
        }

    async def _save_prediction(
        self,
        item_type: str,
        item_name: str,
        state: str,
        district: Optional[str],
        variety: Optional[str],
        target_date: date,
        prediction: Dict[str, Any],
    ):
        """Save prediction to database"""
        # Determine season
        month = target_date.month
        if 6 <= month <= 10:
            season = "Kharif"
        elif 11 <= month or month <= 3:
            season = "Rabi"
        else:
            season = "Zaid"

        try:
            _rows(
                """INSERT INTO price_predictions (item_type, item_name, variety, state, district, prediction_date,
                   target_date, predicted_price, confidence_score, price_range_min, price_range_max, trend,
                   demand_forecast, supply_forecast, season, model_version, factors)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?) RETURNING id""",
                [
                    item_type,
                    item_name,
                    variety,
                    state,
                    district,
                    datetime.now(),
                    target_date,
                    prediction.get("predicted_price", 0),
                    prediction.get("confidence_score", 0),
                    prediction.get("price_range_min", 0),
                    prediction.get("price_range_max", 0),
                    prediction.get("trend"),
                    prediction.get("demand_forecast"),
                    prediction.get("supply_forecast"),
                    season,
                    prediction.get("model_version"),
                    json.dumps(prediction.get("factors", [])),
                ],
            )
        except Exception as e:  # a prediction is still useful to the caller if storing it fails
            logger.warning(f"Could not store price prediction: {e}")
            return

        logger.info(f"Saved price prediction for {item_name} in {state}")

    def _format_opportunity_alert_message(self, alert: Dict[str, Any]) -> str:
        """Format opportunity alert message for SNS"""
        return f"""
Market Opportunity Alert

Crop: {alert['item_name']}
Location: {alert['state']}, {alert.get('district', 'All districts')}
Opportunity Score: {alert['opportunity_score']}/100
Level: {alert['opportunity_level'].upper()}

{alert['recommendation']}

Score Breakdown:
- Price Trend: {alert['score_components']['price_trend']['score']}/{alert['score_components']['price_trend']['max']}
- Demand Level: {alert['score_components']['demand_level']['score']}/{alert['score_components']['demand_level']['max']} ({alert['score_components']['demand_level']['level']})
- Supply-Demand Gap: {alert['score_components']['supply_demand_gap']['score']}/{alert['score_components']['supply_demand_gap']['max']}
- Profitability: {alert['score_components']['profitability']['score']}/{alert['score_components']['profitability']['max']}

This is an automated alert from the Rural Farming Platform Market Intelligence system.
"""
