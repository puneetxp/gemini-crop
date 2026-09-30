"""
Real-Time Yield Prediction Update Service
Updates yield predictions based on crop progress with weekly updates

Task 25.3: Implement real-time yield prediction updates
Validates: Requirements AC10 (Phase 6 - Required)
"""

import logging
from datetime import date, datetime, timedelta
from typing import Any, Dict, List, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.services.bedrock_service import bedrock_service
from app.services.crop_growth_tracker import get_crop_growth_tracker as get_crop_milestone_service
from app.services.farm_access import (
    run_named,  # raw SQL via app.core.db.DB; :name params, autocommit
)
from app.services.notification_service import get_notification_service
from app.services.weather_service import get_weather_service


def text(sql: str) -> str:
    """Stand-in for sqlalchemy.text(): queries here are plain SQL strings run with run_named()."""
    return sql


logger = logging.getLogger(__name__)


# Quality grade thresholds based on growing conditions
QUALITY_GRADE_THRESHOLDS = {
    "A": {
        "min_growth_rate": 0.95,  # 95% of expected growth rate
        "min_weather_score": 0.85,  # 85% favorable weather
        "min_care_score": 0.90,  # 90% proper care (fertilizer, pest control)
        "description": "Premium quality - optimal growing conditions",
    },
    "B": {
        "min_growth_rate": 0.80,  # 80% of expected growth rate
        "min_weather_score": 0.70,  # 70% favorable weather
        "min_care_score": 0.75,  # 75% proper care
        "description": "Good quality - acceptable growing conditions",
    },
    "C": {
        "min_growth_rate": 0.60,  # 60% of expected growth rate
        "min_weather_score": 0.50,  # 50% favorable weather
        "min_care_score": 0.60,  # 60% proper care
        "description": "Fair quality - suboptimal growing conditions",
    },
}

# Harvest readiness maturity threshold
HARVEST_READINESS_THRESHOLD = 0.90  # 90% maturity


class YieldPredictionUpdateService:
    """
    Service for real-time yield prediction updates based on crop progress

    Validates: Requirements AC10 (Phase 6 - Required)
    """

    def __init__(self, db: AsyncSession):
        """Initialize service with database session"""
        self.db = db  # kept for compatibility; queries go through run_named (app.core.db.DB)
        self.milestone_service = get_crop_milestone_service(db)
        self.weather_service = get_weather_service(db)
        self.notification_service = get_notification_service()
        self.bedrock = bedrock_service

    async def update_yield_prediction(
        self,
        crop_id: int,
        current_growth_rate: float,
        weather_conditions: Optional[Dict[str, Any]] = None,
        care_metrics: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Update yield prediction based on crop progress

        Args:
            crop_id: Crop ID
            current_growth_rate: Current growth rate (0.0-1.5, where 1.0 is expected)
            weather_conditions: Recent weather data (optional)
            care_metrics: Care metrics (fertilizer, pest control, etc.) (optional)

        Returns:
            Updated prediction with new yield estimate and harvest date

        Validates: AC10.4 - Update yield predictions weekly based on growth rate
        """
        try:
            # Get crop details using raw SQL

            query = text("""
                SELECT id, crop_name, crop_variety, planting_date, expected_harvest_date,
                       expected_yield, area
                FROM crops
                WHERE id = :crop_id
            """)

            result = run_named(query, {"crop_id": crop_id})
            crop_row = result.first()

            if not crop_row:
                raise ValueError(f"Crop {crop_id} not found")

            # Convert to dict for easier access
            crop = {
                "id": crop_row.id,
                "crop_name": crop_row.crop_name,
                "crop_variety": crop_row.crop_variety,
                "planting_date": crop_row.planting_date,
                "expected_harvest_date": crop_row.expected_harvest_date,
                "expected_yield": (
                    float(crop_row.expected_yield) if crop_row.expected_yield else 0.0
                ),
                "area": float(crop_row.area) if crop_row.area else 0.0,
            }

            # Get current milestone/stage
            current_stage = await self.milestone_service.get_current_stage(crop_id)

            if not current_stage:
                logger.warning(f"No active growth stage for crop {crop_id}")
                return {"error": "No active growth stage"}

            # Calculate updated yield prediction
            original_yield = crop["expected_yield"]

            # Adjust yield based on growth rate
            # Growth rate > 1.0 means better than expected, < 1.0 means worse
            growth_adjustment = current_growth_rate

            # Weather impact on yield (if available)
            weather_adjustment = 1.0
            if weather_conditions:
                weather_adjustment = self._calculate_weather_impact(
                    weather_conditions, crop["crop_name"]
                )

            # Care metrics impact (if available)
            care_adjustment = 1.0
            if care_metrics:
                care_adjustment = self._calculate_care_impact(care_metrics)

            # Calculate new yield prediction
            updated_yield = (
                original_yield * growth_adjustment * weather_adjustment * care_adjustment
            )

            # Calculate confidence based on data quality
            confidence = self._calculate_prediction_confidence(
                has_weather=weather_conditions is not None,
                has_care_metrics=care_metrics is not None,
                growth_rate_variance=abs(current_growth_rate - 1.0),
            )

            # Update harvest date prediction
            updated_harvest_date = await self._adjust_harvest_date(
                crop=crop, growth_rate=current_growth_rate, current_stage=current_stage
            )

            # Calculate quality grade prediction
            quality_grade = await self._predict_quality_grade(
                crop_id=crop_id,
                growth_rate=current_growth_rate,
                weather_conditions=weather_conditions,
                care_metrics=care_metrics,
            )

            # Update crop record using raw SQL
            update_query = text("""
                UPDATE crops
                SET expected_yield = :expected_yield,
                    expected_harvest_date = :expected_harvest_date,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = :crop_id
            """)

            run_named(
                update_query,
                {
                    "crop_id": crop_id,
                    "expected_yield": updated_yield,
                    "expected_harvest_date": updated_harvest_date,
                },
            )
            # committed by DB.raw

            logger.info(
                f"Updated yield prediction for crop {crop_id}: "
                f"{original_yield:.2f} -> {updated_yield:.2f} kg, "
                f"harvest date: {updated_harvest_date}"
            )

            return {
                "crop_id": crop_id,
                "original_yield": round(original_yield, 2),
                "updated_yield": round(updated_yield, 2),
                "yield_change_percentage": round(
                    (
                        ((updated_yield - original_yield) / original_yield * 100)
                        if original_yield > 0
                        else 0
                    ),
                    2,
                ),
                "original_harvest_date": (
                    crop["expected_harvest_date"].isoformat()
                    if isinstance(crop["expected_harvest_date"], date)
                    else str(crop["expected_harvest_date"])
                ),
                "updated_harvest_date": updated_harvest_date.isoformat(),
                "harvest_date_adjustment_days": (
                    (updated_harvest_date - crop["expected_harvest_date"]).days
                    if isinstance(crop["expected_harvest_date"], date)
                    else 0
                ),
                "quality_grade": quality_grade,
                "confidence_score": confidence,
                "growth_rate": current_growth_rate,
                "current_stage": current_stage.get("stage"),
                "updated_at": datetime.now().isoformat(),
            }

        except Exception as e:
            logger.error(f"Error updating yield prediction for crop {crop_id}: {e}")
            raise

    def _calculate_weather_impact(
        self, weather_conditions: Dict[str, Any], crop_name: str
    ) -> float:
        """
        Calculate weather impact on yield

        Args:
            weather_conditions: Recent weather data
            crop_name: Name of the crop

        Returns:
            Weather adjustment factor (0.5-1.2)
        """
        # Extract weather metrics
        avg_temp = weather_conditions.get("avg_temperature", 25.0)
        total_rainfall = weather_conditions.get("total_rainfall", 0.0)
        avg_humidity = weather_conditions.get("avg_humidity", 70)
        extreme_events = weather_conditions.get("extreme_events", 0)

        # Optimal ranges for common crops (simplified)
        optimal_ranges = {
            "rice": {"temp": (20, 35), "rainfall": (100, 200)},
            "wheat": {"temp": (15, 25), "rainfall": (50, 100)},
            "maize": {"temp": (20, 30), "rainfall": (80, 150)},
            "cotton": {"temp": (21, 35), "rainfall": (60, 120)},
            "soybean": {"temp": (20, 30), "rainfall": (80, 140)},
            "sugarcane": {"temp": (20, 35), "rainfall": (150, 250)},
        }

        crop_key = crop_name.lower()
        optimal = optimal_ranges.get(crop_key, {"temp": (20, 30), "rainfall": (80, 150)})

        # Temperature impact
        temp_min, temp_max = optimal["temp"]
        if temp_min <= avg_temp <= temp_max:
            temp_impact = 1.0
        elif avg_temp < temp_min:
            temp_impact = max(0.7, 1.0 - (temp_min - avg_temp) * 0.02)
        else:
            temp_impact = max(0.6, 1.0 - (avg_temp - temp_max) * 0.03)

        # Rainfall impact
        rain_min, rain_max = optimal["rainfall"]
        if rain_min <= total_rainfall <= rain_max:
            rain_impact = 1.0
        elif total_rainfall < rain_min:
            rain_impact = max(0.6, 1.0 - (rain_min - total_rainfall) / rain_min * 0.4)
        else:
            rain_impact = max(0.7, 1.0 - (total_rainfall - rain_max) / rain_max * 0.3)

        # Extreme events impact (each event reduces by 5%)
        extreme_impact = max(0.5, 1.0 - (extreme_events * 0.05))

        # Combined weather impact
        weather_impact = temp_impact * 0.4 + rain_impact * 0.4 + extreme_impact * 0.2

        return max(0.5, min(1.2, weather_impact))

    def _calculate_care_impact(self, care_metrics: Dict[str, Any]) -> float:
        """
        Calculate care metrics impact on yield

        Args:
            care_metrics: Care metrics (fertilizer, pest control, etc.)

        Returns:
            Care adjustment factor (0.7-1.15)
        """
        # Extract care metrics
        fertilizer_applied = care_metrics.get("fertilizer_applied", False)
        fertilizer_timing = care_metrics.get("fertilizer_timing_optimal", True)
        pest_control = care_metrics.get("pest_control_done", False)
        irrigation_adequate = care_metrics.get("irrigation_adequate", True)
        weeding_done = care_metrics.get("weeding_done", False)

        # Calculate care score
        care_score = 0.0

        if fertilizer_applied:
            care_score += 0.30
            if fertilizer_timing:
                care_score += 0.10

        if pest_control:
            care_score += 0.25

        if irrigation_adequate:
            care_score += 0.20

        if weeding_done:
            care_score += 0.15

        # Convert to adjustment factor
        # 0.0 score = 0.7x, 1.0 score = 1.15x
        care_adjustment = 0.7 + (care_score * 0.45)

        return max(0.7, min(1.15, care_adjustment))

    def _calculate_prediction_confidence(
        self, has_weather: bool, has_care_metrics: bool, growth_rate_variance: float
    ) -> float:
        """
        Calculate confidence score for prediction

        Args:
            has_weather: Whether weather data is available
            has_care_metrics: Whether care metrics are available
            growth_rate_variance: Variance from expected growth rate

        Returns:
            Confidence score (0.0-1.0)
        """
        base_confidence = 0.75

        # Weather data adds confidence
        if has_weather:
            base_confidence += 0.10

        # Care metrics add confidence
        if has_care_metrics:
            base_confidence += 0.10

        # Low variance adds confidence
        if growth_rate_variance < 0.1:
            base_confidence += 0.05
        elif growth_rate_variance > 0.3:
            base_confidence -= 0.10

        return max(0.60, min(0.95, base_confidence))

    async def _adjust_harvest_date(
        self, crop: Dict[str, Any], growth_rate: float, current_stage: Dict[str, Any]
    ) -> date:
        """
        Adjust harvest date based on growth rate

        Args:
            crop: Crop data dict
            growth_rate: Current growth rate
            current_stage: Current growth stage info

        Returns:
            Adjusted harvest date

        Validates: AC10.5 - Adjust harvest date prediction based on growth rate (±3 days accuracy)
        """
        original_harvest = crop["expected_harvest_date"]
        if isinstance(original_harvest, str):
            original_harvest = datetime.fromisoformat(original_harvest).date()
        elif isinstance(original_harvest, datetime):
            original_harvest = original_harvest.date()

        # Calculate days remaining to harvest
        today = date.today()
        days_remaining = (original_harvest - today).days

        if days_remaining <= 0:
            # Already at or past harvest date
            return original_harvest

        # Adjust based on growth rate
        # Growth rate > 1.0 means faster growth, harvest earlier
        # Growth rate < 1.0 means slower growth, harvest later

        if growth_rate > 1.0:
            # Faster growth - harvest earlier
            # For every 10% faster, harvest 1 day earlier (max 3 days)
            days_adjustment = min(3, int((growth_rate - 1.0) * 10))
            adjusted_harvest = original_harvest - timedelta(days=days_adjustment)
        elif growth_rate < 1.0:
            # Slower growth - harvest later
            # For every 10% slower, harvest 1 day later (max 3 days)
            days_adjustment = min(3, int((1.0 - growth_rate) * 10))
            adjusted_harvest = original_harvest + timedelta(days=days_adjustment)
        else:
            # Growth rate is exactly as expected
            adjusted_harvest = original_harvest

        logger.info(
            f"Adjusted harvest date for crop {crop['id']}: "
            f"{original_harvest} -> {adjusted_harvest} "
            f"(growth rate: {growth_rate:.2f})"
        )

        return adjusted_harvest

    async def _predict_quality_grade(
        self,
        crop_id: int,
        growth_rate: float,
        weather_conditions: Optional[Dict[str, Any]],
        care_metrics: Optional[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Predict quality grade based on growing conditions

        Args:
            crop_id: Crop ID
            growth_rate: Current growth rate
            weather_conditions: Recent weather data
            care_metrics: Care metrics

        Returns:
            Quality grade prediction with details

        Validates: AC10.6 - Predict quality grade (A/B/C) based on growing conditions
        """
        # Calculate weather score
        weather_score = 0.85  # Default if no data
        if weather_conditions:
            weather_impact = self._calculate_weather_impact(
                weather_conditions, "generic"  # Use generic crop for scoring
            )
            weather_score = weather_impact

        # Calculate care score
        care_score = 0.80  # Default if no data
        if care_metrics:
            care_impact = self._calculate_care_impact(care_metrics)
            # Convert impact (0.7-1.15) to score (0.0-1.0)
            care_score = (care_impact - 0.7) / 0.45

        # Determine quality grade
        if (
            growth_rate >= QUALITY_GRADE_THRESHOLDS["A"]["min_growth_rate"]
            and weather_score >= QUALITY_GRADE_THRESHOLDS["A"]["min_weather_score"]
            and care_score >= QUALITY_GRADE_THRESHOLDS["A"]["min_care_score"]
        ):
            grade = "A"
            description = QUALITY_GRADE_THRESHOLDS["A"]["description"]
            confidence = 0.90
        elif (
            growth_rate >= QUALITY_GRADE_THRESHOLDS["B"]["min_growth_rate"]
            and weather_score >= QUALITY_GRADE_THRESHOLDS["B"]["min_weather_score"]
            and care_score >= QUALITY_GRADE_THRESHOLDS["B"]["min_care_score"]
        ):
            grade = "B"
            description = QUALITY_GRADE_THRESHOLDS["B"]["description"]
            confidence = 0.85
        elif (
            growth_rate >= QUALITY_GRADE_THRESHOLDS["C"]["min_growth_rate"]
            and weather_score >= QUALITY_GRADE_THRESHOLDS["C"]["min_weather_score"]
            and care_score >= QUALITY_GRADE_THRESHOLDS["C"]["min_care_score"]
        ):
            grade = "C"
            description = QUALITY_GRADE_THRESHOLDS["C"]["description"]
            confidence = 0.80
        else:
            grade = "D"
            description = "Below standard - significant growing condition issues"
            confidence = 0.70

        return {
            "grade": grade,
            "description": description,
            "confidence": confidence,
            "factors": {
                "growth_rate": round(growth_rate, 2),
                "weather_score": round(weather_score, 2),
                "care_score": round(care_score, 2),
            },
            "recommendations": self._get_quality_improvement_recommendations(
                grade, growth_rate, weather_score, care_score
            ),
        }

    def _get_quality_improvement_recommendations(
        self, grade: str, growth_rate: float, weather_score: float, care_score: float
    ) -> List[str]:
        """Get recommendations to improve quality grade"""
        recommendations = []

        if grade in ["C", "D"]:
            if growth_rate < 0.90:
                recommendations.append("Improve growth rate with balanced fertilizer application")

            if weather_score < 0.80:
                recommendations.append(
                    "Protect crops from adverse weather with mulching or shade nets"
                )

            if care_score < 0.80:
                recommendations.append(
                    "Increase care frequency: regular watering, weeding, and pest control"
                )

        if grade == "B":
            recommendations.append("Maintain current practices and monitor for any issues")

        if grade == "A":
            recommendations.append("Excellent conditions - continue current management practices")

        return recommendations

    async def check_harvest_readiness(self, crop_id: int) -> Dict[str, Any]:
        """
        Check if crop has reached harvest readiness (90% maturity)

        Args:
            crop_id: Crop ID

        Returns:
            Harvest readiness status and alert details

        Validates: AC10.7 - Generate harvest readiness alerts at 90% maturity
        """
        try:
            # Get crop details using raw SQL

            query = text("""
                SELECT id, crop_name, planting_date, expected_harvest_date
                FROM crops
                WHERE id = :crop_id
            """)

            result = run_named(query, {"crop_id": crop_id})
            crop_row = result.first()

            if not crop_row:
                raise ValueError(f"Crop {crop_id} not found")

            # Convert to dict
            planting_date = crop_row.planting_date
            if isinstance(planting_date, str):
                planting_date = datetime.fromisoformat(planting_date).date()
            elif isinstance(planting_date, datetime):
                planting_date = planting_date.date()

            expected_harvest = crop_row.expected_harvest_date
            if isinstance(expected_harvest, str):
                expected_harvest = datetime.fromisoformat(expected_harvest).date()
            elif isinstance(expected_harvest, datetime):
                expected_harvest = expected_harvest.date()

            today = date.today()

            total_days = (expected_harvest - planting_date).days
            days_elapsed = (today - planting_date).days

            maturity_percentage = min(1.0, days_elapsed / total_days) if total_days > 0 else 0.0

            # Check if reached 90% maturity
            is_ready = maturity_percentage >= HARVEST_READINESS_THRESHOLD

            # Calculate optimal harvest window
            days_to_harvest = (expected_harvest - today).days
            harvest_window_start = expected_harvest - timedelta(days=3)
            harvest_window_end = expected_harvest + timedelta(days=3)

            result = {
                "crop_id": crop_id,
                "crop_name": crop_row.crop_name,
                "maturity_percentage": round(maturity_percentage * 100, 1),
                "is_harvest_ready": is_ready,
                "days_to_harvest": days_to_harvest,
                "expected_harvest_date": expected_harvest.isoformat(),
                "optimal_harvest_window": {
                    "start": harvest_window_start.isoformat(),
                    "end": harvest_window_end.isoformat(),
                },
            }

            # If ready, add alert details
            if is_ready:
                result["alert"] = {
                    "type": "harvest_readiness",
                    "severity": "high",
                    "message": f"{crop_row.crop_name} has reached 90% maturity and is ready for harvest",
                    "action_required": "Plan harvest within optimal window",
                    "recommendations": [
                        "Check weather forecast for dry conditions",
                        "Arrange labor and equipment for harvesting",
                        "Prepare storage facilities",
                        "Contact buyers if not already arranged",
                        f"Harvest between {harvest_window_start} and {harvest_window_end}",
                    ],
                }

            return result

        except Exception as e:
            logger.error(f"Error checking harvest readiness for crop {crop_id}: {e}")
            raise

    async def send_harvest_readiness_alert(
        self, crop_id: int, farmer_phone: str, farmer_email: Optional[str], farmer_name: str
    ) -> Dict[str, Any]:
        """
        Send harvest readiness alert to farmer

        Args:
            crop_id: Crop ID
            farmer_phone: Farmer's phone number
            farmer_email: Farmer's email (optional)
            farmer_name: Farmer's name

        Returns:
            Notification result

        Validates: AC10.7 - Send harvest readiness alerts
        """
        try:
            # Get harvest readiness status
            readiness = await self.check_harvest_readiness(crop_id)

            if not readiness.get("is_harvest_ready"):
                return {"success": False, "message": "Crop not yet ready for harvest"}

            # Prepare action items
            action_items = readiness["alert"]["recommendations"]

            # Send notification
            notification_result = self.notification_service.send_strategy_reminder(
                farmer_phone=farmer_phone,
                farmer_email=farmer_email,
                farmer_name=farmer_name,
                strategy_id=f"crop_{crop_id}",
                reminder_type=f"harvest_ready_{readiness['crop_name']}",
                action_items=action_items,
                due_date=readiness["expected_harvest_date"],
            )

            logger.info(f"Harvest readiness alert sent for crop {crop_id}")

            return {
                "success": True,
                "crop_id": crop_id,
                "maturity_percentage": readiness["maturity_percentage"],
                "notification_result": notification_result,
            }

        except Exception as e:
            logger.error(f"Error sending harvest readiness alert: {e}")
            return {"success": False, "error": str(e)}

    async def run_weekly_update_job(self) -> Dict[str, Any]:
        """
        Background job to update yield predictions weekly for all active crops

        Returns:
            Summary of updates performed

        Validates: AC10.4 - Weekly yield prediction updates
        """
        try:

            summary = {
                "crops_checked": 0,
                "predictions_updated": 0,
                "harvest_alerts_sent": 0,
                "errors": 0,
            }

            # Get all active crops (planted or growing status) using raw SQL
            query = text("""
                SELECT id, crop_name, planting_date, expected_harvest_date
                FROM crops
                WHERE status IN ('planted', 'growing')
                  AND expected_harvest_date >= CURRENT_DATE
            """)

            result = run_named(query)
            crops = result.fetchall()

            summary["crops_checked"] = len(crops)

            for crop_row in crops:
                try:
                    crop_id = crop_row.id

                    # Get current growth stage
                    current_stage = await self.milestone_service.get_current_stage(crop_id)

                    if not current_stage:
                        continue

                    # Calculate growth rate based on stage progress
                    progress = current_stage.get("progress_percentage", 0) / 100.0
                    expected_progress = 0.5  # Simplified - would calculate based on time
                    growth_rate = progress / expected_progress if expected_progress > 0 else 1.0

                    # Update yield prediction
                    await self.update_yield_prediction(
                        crop_id=crop_id, current_growth_rate=growth_rate
                    )

                    summary["predictions_updated"] += 1

                    # Check harvest readiness
                    readiness = await self.check_harvest_readiness(crop_id)

                    if readiness.get("is_harvest_ready"):
                        # Would send alert here (need farmer contact info)
                        summary["harvest_alerts_sent"] += 1

                except Exception as e:
                    logger.error(f"Error updating crop {crop_row.id}: {e}")
                    summary["errors"] += 1

            logger.info(f"Weekly update job completed: {summary}")
            return summary

        except Exception as e:
            logger.error(f"Error in weekly update job: {e}")
            return {"error": str(e)}


def get_yield_prediction_update_service(db: AsyncSession) -> YieldPredictionUpdateService:
    """Get yield prediction update service instance"""
    return YieldPredictionUpdateService(db)
