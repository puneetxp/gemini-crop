"""
Weather-Based Recommendations Service
Implements weather-aware farming recommendations for optimal crop management

Task 23.3: Build weather-based recommendations
Validates: Requirements AC8 (Phase 6 - Required)
"""

import logging
from datetime import date, datetime, timedelta
from typing import Any  # db kept for compatibility; queries use app.core.db.DB
from typing import Any as AsyncSession
from typing import Dict, List, Optional

from app.services.farm_access import crop_for_user, farm_for_user, fetch_one
from app.services.severe_weather_service import SevereWeatherService
from app.services.weather_service import WeatherService

logger = logging.getLogger(__name__)


class WeatherRecommendationsService:
    """
    Weather-based recommendations for farming operations

    Features:
    - Weather-aware planting recommendations (optimal planting windows)
    - Optimal harvest timing (avoid rain during harvest)
    - Irrigation scheduling (reduce water waste)
    - Weather-based crop care (pest control, fertilizer timing)
    """

    # Rainfall thresholds
    LIGHT_RAIN = 5.0  # mm per day
    MODERATE_RAIN = 15.0  # mm per day
    HEAVY_RAIN = 50.0  # mm per day

    # Temperature thresholds for crop activities
    MIN_PLANTING_TEMP = 15.0  # °C
    MAX_PLANTING_TEMP = 35.0  # °C
    OPTIMAL_FERTILIZER_TEMP_MIN = 18.0  # °C
    OPTIMAL_FERTILIZER_TEMP_MAX = 32.0  # °C

    def __init__(
        self,
        db: AsyncSession,
        weather_service: WeatherService,
        severe_weather_service: SevereWeatherService,
    ):
        """
        Initialize weather recommendations service

        Args:
            db: Database session
            weather_service: Weather service instance
            severe_weather_service: Severe weather service instance
        """
        self.db = db
        self.weather_service = weather_service
        self.severe_weather_service = severe_weather_service

    async def get_planting_recommendations(
        self, latitude: float, longitude: float, crop_type: str, season: str
    ) -> Dict[str, Any]:
        """
        Generate weather-aware planting recommendations

        Args:
            latitude: GPS latitude
            longitude: GPS longitude
            crop_type: Type of crop to plant
            season: Growing season (kharif, rabi, zaid)

        Returns:
            Planting recommendations with optimal windows
        """
        # Get 14-day forecast for planting window analysis
        forecast_data = await self.weather_service.get_forecast(
            latitude, longitude, days=14, use_cache=True
        )

        if not forecast_data or not forecast_data.get("forecasts"):
            logger.warning("No forecast data available for planting recommendations")
            return {
                "status": "unavailable",
                "message": "Weather forecast unavailable. Please try again later.",
            }

        # Analyze forecast for optimal planting windows
        planting_windows = []
        current_window = None

        for forecast in forecast_data["forecasts"]:
            date_obj = forecast["date"]
            rainfall = forecast.get("rainfall", 0)
            temp_max = forecast.get("temp_max", 0)
            temp_min = forecast.get("temp_min", 0)

            # Check if conditions are suitable for planting
            is_suitable = (
                rainfall < self.MODERATE_RAIN  # Not too much rain
                and self.MIN_PLANTING_TEMP <= temp_min  # Not too cold
                and temp_max <= self.MAX_PLANTING_TEMP  # Not too hot
            )

            if is_suitable:
                if current_window is None:
                    current_window = {
                        "start_date": date_obj,
                        "end_date": date_obj,
                        "days": 1,
                        "avg_rainfall": rainfall,
                        "avg_temp": (temp_min + temp_max) / 2,
                    }
                else:
                    current_window["end_date"] = date_obj
                    current_window["days"] += 1
                    current_window["avg_rainfall"] = (current_window["avg_rainfall"] + rainfall) / 2
                    current_window["avg_temp"] = (
                        current_window["avg_temp"] + (temp_min + temp_max) / 2
                    ) / 2
            else:
                if current_window and current_window["days"] >= 2:
                    planting_windows.append(current_window)
                current_window = None

        # Add final window if exists
        if current_window and current_window["days"] >= 2:
            planting_windows.append(current_window)

        # Calculate suitability scores
        for window in planting_windows:
            window["suitability_score"] = self._calculate_planting_suitability(
                window, crop_type, season
            )

        # Sort by suitability
        planting_windows.sort(key=lambda x: x["suitability_score"], reverse=True)

        # Generate recommendation
        recommendation = self._generate_planting_recommendation(
            planting_windows, crop_type, season, forecast_data
        )

        return {
            "crop_type": crop_type,
            "season": season,
            "latitude": latitude,
            "longitude": longitude,
            "planting_windows": planting_windows,
            "optimal_window": planting_windows[0] if planting_windows else None,
            "recommendation": recommendation,
            "forecast_period": f"{forecast_data['forecasts'][0]['date']} to {forecast_data['forecasts'][-1]['date']}",
        }

    async def get_harvest_timing_recommendations(
        self,
        farm_id: int,
        crop_id: int,
        expected_harvest_date: date,
        user=None,
    ) -> Dict[str, Any]:
        """
        Generate optimal harvest timing based on weather windows

        Args:
            farm_id: Farm ID
            crop_id: Crop ID
            expected_harvest_date: Expected harvest date

        Returns:
            Harvest timing recommendations with dry windows
        """
        # Get farm and crop details (raw SQL; owner-checked when `user` is given -> LookupError)
        if user is not None:
            farm = farm_for_user(farm_id, user)
            crop = crop_for_user(crop_id, user)
            if crop.farm_id != farm_id:
                raise LookupError(f"Crop {crop_id} not found")
        else:
            farm = fetch_one("SELECT * FROM farms WHERE id = ?", [farm_id])
            if not farm:
                logger.error(f"Farm {farm_id} not found")
                return {"status": "error", "message": "Farm not found"}
            try:
                crop = crop_for_user(crop_id, None)
            except LookupError:
                crop = None

        if not crop:
            logger.error(f"Crop {crop_id} not found")
            return {"status": "error", "message": "Crop not found"}

        # Get GPS coordinates
        latitude = float(farm.latitude) if farm.latitude else None
        longitude = float(farm.longitude) if farm.longitude else None

        if not latitude or not longitude:
            logger.warning(f"Farm {farm_id} has no GPS coordinates")
            return {
                "status": "limited",
                "message": "GPS coordinates not available. Using general recommendations.",
            }

        # Use severe weather service to analyze harvest windows
        harvest_windows = await self.severe_weather_service.analyze_harvest_windows(
            latitude, longitude, days_ahead=14
        )

        # Check for emergency harvest needs
        emergency_alert = await self.severe_weather_service.check_emergency_harvest_alert(
            farm_id, crop_id, user=user
        )

        # Calculate days until expected harvest
        days_to_harvest = (expected_harvest_date - datetime.now().date()).days

        return {
            "farm_id": farm_id,
            "crop_id": crop_id,
            "crop_type": crop.crop_name,
            "expected_harvest_date": expected_harvest_date,
            "days_to_harvest": days_to_harvest,
            "harvest_windows": harvest_windows,
            "emergency_alert": emergency_alert,
            "recommendation": self._generate_harvest_timing_recommendation(
                harvest_windows, emergency_alert, days_to_harvest
            ),
        }

    async def get_irrigation_schedule(
        self, latitude: float, longitude: float, crop_type: str, soil_type: str, days_ahead: int = 7
    ) -> Dict[str, Any]:
        """
        Generate irrigation schedule based on rainfall forecasts

        Args:
            latitude: GPS latitude
            longitude: GPS longitude
            crop_type: Type of crop
            soil_type: Soil type (sandy, loamy, clay)
            days_ahead: Number of days to schedule (default: 7)

        Returns:
            Irrigation schedule with water-saving recommendations
        """
        # Get weather forecast
        forecast_data = await self.weather_service.get_forecast(
            latitude, longitude, days=days_ahead, use_cache=True
        )

        if not forecast_data or not forecast_data.get("forecasts"):
            logger.warning("No forecast data available for irrigation scheduling")
            return {
                "status": "unavailable",
                "message": "Weather forecast unavailable. Use standard irrigation schedule.",
            }

        # Analyze daily irrigation needs
        irrigation_schedule = []
        total_water_saved = 0.0

        for forecast in forecast_data["forecasts"]:
            date_obj = forecast["date"]
            rainfall = forecast.get("rainfall", 0)
            temp_max = forecast.get("temp_max", 0)
            humidity = forecast.get("humidity", 0)

            # Calculate base water requirement (mm per day)
            base_requirement = self._calculate_base_water_requirement(crop_type, temp_max, humidity)

            # Adjust for soil type
            soil_factor = self._get_soil_water_retention_factor(soil_type)
            adjusted_requirement = base_requirement * soil_factor

            # Subtract expected rainfall
            net_requirement = max(0, adjusted_requirement - rainfall)

            # Determine irrigation recommendation
            if rainfall >= self.HEAVY_RAIN:
                irrigation_needed = False
                recommendation = "No irrigation needed - heavy rain expected"
                water_saved = adjusted_requirement
            elif rainfall >= self.MODERATE_RAIN:
                irrigation_needed = False
                recommendation = "No irrigation needed - moderate rain expected"
                water_saved = adjusted_requirement
            elif rainfall >= self.LIGHT_RAIN:
                irrigation_needed = net_requirement > 5
                recommendation = f"Light irrigation if needed ({net_requirement:.1f}mm)"
                water_saved = rainfall
            else:
                irrigation_needed = True
                recommendation = f"Full irrigation required ({net_requirement:.1f}mm)"
                water_saved = 0

            total_water_saved += water_saved

            irrigation_schedule.append(
                {
                    "date": date_obj,
                    "rainfall_forecast": rainfall,
                    "temperature": temp_max,
                    "humidity": humidity,
                    "base_water_requirement": base_requirement,
                    "net_water_requirement": net_requirement,
                    "irrigation_needed": irrigation_needed,
                    "recommendation": recommendation,
                    "water_saved": water_saved,
                }
            )

        return {
            "latitude": latitude,
            "longitude": longitude,
            "crop_type": crop_type,
            "soil_type": soil_type,
            "schedule_period": f"{irrigation_schedule[0]['date']} to {irrigation_schedule[-1]['date']}",
            "irrigation_schedule": irrigation_schedule,
            "total_water_saved": total_water_saved,
            "water_savings_percentage": (total_water_saved / (len(irrigation_schedule) * 10)) * 100,
            "summary": self._generate_irrigation_summary(irrigation_schedule, total_water_saved),
        }

    async def get_crop_care_recommendations(
        self,
        latitude: float,
        longitude: float,
        crop_type: str,
        growth_stage: str,
        days_ahead: int = 7,
    ) -> Dict[str, Any]:
        """
        Generate weather-based crop care recommendations

        Args:
            latitude: GPS latitude
            longitude: GPS longitude
            crop_type: Type of crop
            growth_stage: Current growth stage (germination, vegetative, flowering, maturation)
            days_ahead: Number of days to plan (default: 7)

        Returns:
            Crop care recommendations for pest control and fertilizer application
        """
        # Get weather forecast
        forecast_data = await self.weather_service.get_forecast(
            latitude, longitude, days=days_ahead, use_cache=True
        )

        if not forecast_data or not forecast_data.get("forecasts"):
            logger.warning("No forecast data available for crop care recommendations")
            return {
                "status": "unavailable",
                "message": "Weather forecast unavailable. Use standard care schedule.",
            }

        # Analyze weather for crop care activities
        care_recommendations = []

        for forecast in forecast_data["forecasts"]:
            date_obj = forecast["date"]
            rainfall = forecast.get("rainfall", 0)
            temp_max = forecast.get("temp_max", 0)
            temp_min = forecast.get("temp_min", 0)
            humidity = forecast.get("humidity", 0)

            daily_recommendations = {
                "date": date_obj,
                "weather_summary": self._get_weather_summary(forecast),
                "fertilizer_application": self._get_fertilizer_timing_recommendation(
                    rainfall, temp_max, temp_min, humidity, growth_stage
                ),
                "pest_control": self._get_pest_control_recommendation(
                    rainfall, temp_max, humidity, crop_type, growth_stage
                ),
                "general_care": self._get_general_care_recommendation(
                    rainfall, temp_max, temp_min, humidity, growth_stage
                ),
            }

            care_recommendations.append(daily_recommendations)

        # Identify optimal days for specific activities
        optimal_fertilizer_days = [
            rec["date"] for rec in care_recommendations if rec["fertilizer_application"]["suitable"]
        ]

        optimal_pest_control_days = [
            rec["date"] for rec in care_recommendations if rec["pest_control"]["suitable"]
        ]

        return {
            "latitude": latitude,
            "longitude": longitude,
            "crop_type": crop_type,
            "growth_stage": growth_stage,
            "forecast_period": f"{care_recommendations[0]['date']} to {care_recommendations[-1]['date']}",
            "daily_recommendations": care_recommendations,
            "optimal_fertilizer_days": optimal_fertilizer_days,
            "optimal_pest_control_days": optimal_pest_control_days,
            "summary": self._generate_crop_care_summary(
                care_recommendations, optimal_fertilizer_days, optimal_pest_control_days
            ),
        }

    # Helper methods

    def _calculate_planting_suitability(
        self, window: Dict[str, Any], crop_type: str, season: str
    ) -> float:
        """Calculate suitability score for planting window"""
        score = 0.0

        # Days score (longer window is better, max 40 points)
        days = window["days"]
        score += min(days * 8, 40)

        # Rainfall score (light rain is good, max 30 points)
        rainfall = window["avg_rainfall"]
        if rainfall < 5:
            score += 30
        elif rainfall < 10:
            score += 20
        else:
            score += 10

        # Temperature score (optimal range, max 30 points)
        temp = window["avg_temp"]
        if 20 <= temp <= 30:
            score += 30
        elif 18 <= temp < 20 or 30 < temp <= 32:
            score += 20
        else:
            score += 10

        return score

    def _generate_planting_recommendation(
        self,
        windows: List[Dict[str, Any]],
        crop_type: str,
        season: str,
        forecast_data: Dict[str, Any],
    ) -> str:
        """Generate planting recommendation text"""
        if not windows:
            return (
                f"No optimal planting windows found in the next 14 days. "
                f"Weather conditions are not favorable for {crop_type} planting. "
                f"Monitor forecast and wait for suitable conditions."
            )

        optimal = windows[0]
        start = optimal["start_date"].strftime("%B %d")
        end = optimal["end_date"].strftime("%B %d")
        days = optimal["days"]

        return (
            f"Optimal planting window for {crop_type}: {start} to {end} ({days} days). "
            f"Expected rainfall: {optimal['avg_rainfall']:.1f}mm/day, "
            f"Temperature: {optimal['avg_temp']:.1f}°C. "
            f"Prepare soil and seeds in advance for timely planting."
        )

    def _generate_harvest_timing_recommendation(
        self,
        harvest_windows: Dict[str, Any],
        emergency_alert: Optional[Dict[str, Any]],
        days_to_harvest: int,
    ) -> str:
        """Generate harvest timing recommendation"""
        if emergency_alert:
            return emergency_alert.get("recommendation", "Emergency harvest recommended")

        if not harvest_windows or not harvest_windows.get("dry_periods"):
            return (
                f"No clear dry periods in forecast. Monitor weather closely and "
                f"harvest when conditions permit. Expected harvest in {days_to_harvest} days."
            )

        optimal = harvest_windows.get("optimal_window")
        if optimal:
            start = optimal["start_date"].strftime("%B %d")
            end = optimal["end_date"].strftime("%B %d")
            return (
                f"Optimal harvest window: {start} to {end} ({optimal['days']} dry days). "
                f"Plan harvest operations during this period to avoid rain damage. "
                f"Temperature: {optimal['avg_temp']:.1f}°C, Humidity: {optimal['avg_humidity']:.0f}%."
            )

        return f"Monitor weather forecast. Expected harvest in {days_to_harvest} days."

    def _calculate_base_water_requirement(
        self, crop_type: str, temperature: float, humidity: int
    ) -> float:
        """Calculate base water requirement in mm per day"""
        # Base requirement varies by crop type
        base_requirements = {
            "rice": 12.0,
            "wheat": 8.0,
            "maize": 10.0,
            "cotton": 9.0,
            "sugarcane": 15.0,
            "vegetables": 7.0,
            "pulses": 6.0,
        }

        base = base_requirements.get(crop_type.lower(), 8.0)

        # Adjust for temperature (higher temp = more water)
        if temperature > 35:
            base *= 1.3
        elif temperature > 30:
            base *= 1.15
        elif temperature < 20:
            base *= 0.85

        # Adjust for humidity (lower humidity = more water)
        if humidity < 40:
            base *= 1.2
        elif humidity < 60:
            base *= 1.1
        elif humidity > 80:
            base *= 0.9

        return base

    def _get_soil_water_retention_factor(self, soil_type: str) -> float:
        """Get water retention factor for soil type"""
        factors = {
            "sandy": 1.3,  # Poor retention, needs more water
            "loamy": 1.0,  # Good retention, standard
            "clay": 0.8,  # Excellent retention, needs less water
        }
        return factors.get(soil_type.lower(), 1.0)

    def _generate_irrigation_summary(
        self, schedule: List[Dict[str, Any]], total_water_saved: float
    ) -> str:
        """Generate irrigation schedule summary"""
        irrigation_days = sum(1 for day in schedule if day["irrigation_needed"])
        no_irrigation_days = len(schedule) - irrigation_days

        return (
            f"Irrigation needed on {irrigation_days} of {len(schedule)} days. "
            f"Expected water savings: {total_water_saved:.1f}mm "
            f"({(total_water_saved / (len(schedule) * 10)) * 100:.1f}% reduction). "
            f"Rainfall will provide natural irrigation on {no_irrigation_days} days."
        )

    def _get_weather_summary(self, forecast: Dict[str, Any]) -> str:
        """Generate weather summary for a day"""
        rainfall = forecast.get("rainfall", 0)
        temp_max = forecast.get("temp_max", 0)
        humidity = forecast.get("humidity", 0)

        if rainfall >= self.HEAVY_RAIN:
            weather = "Heavy rain"
        elif rainfall >= self.MODERATE_RAIN:
            weather = "Moderate rain"
        elif rainfall >= self.LIGHT_RAIN:
            weather = "Light rain"
        else:
            weather = "Dry"

        return f"{weather}, {temp_max:.1f}°C, {humidity}% humidity"

    def _get_fertilizer_timing_recommendation(
        self, rainfall: float, temp_max: float, temp_min: float, humidity: int, growth_stage: str
    ) -> Dict[str, Any]:
        """Get fertilizer application timing recommendation"""
        # Check if conditions are suitable
        suitable = True
        reasons = []

        # Avoid application before heavy rain (nutrient loss)
        if rainfall >= self.MODERATE_RAIN:
            suitable = False
            reasons.append(f"Heavy rain expected ({rainfall:.1f}mm) - nutrients will wash away")

        # Check temperature range
        if not (self.OPTIMAL_FERTILIZER_TEMP_MIN <= temp_max <= self.OPTIMAL_FERTILIZER_TEMP_MAX):
            suitable = False
            if temp_max > self.OPTIMAL_FERTILIZER_TEMP_MAX:
                reasons.append(f"Too hot ({temp_max:.1f}°C) - risk of fertilizer burn")
            else:
                reasons.append(f"Too cold ({temp_max:.1f}°C) - slow nutrient uptake")

        # Light rain is actually good for fertilizer application
        if 0 < rainfall < self.LIGHT_RAIN and suitable:
            reasons.append("Light rain will help nutrient absorption")

        if suitable:
            recommendation = "Good day for fertilizer application"
            if growth_stage == "vegetative":
                recommendation += " - focus on nitrogen-rich fertilizers"
            elif growth_stage == "flowering":
                recommendation += " - focus on phosphorus and potassium"
        else:
            recommendation = "Avoid fertilizer application - " + "; ".join(reasons)

        return {"suitable": suitable, "recommendation": recommendation, "reasons": reasons}

    def _get_pest_control_recommendation(
        self, rainfall: float, temperature: float, humidity: int, crop_type: str, growth_stage: str
    ) -> Dict[str, Any]:
        """Get pest control timing recommendation"""
        suitable = True
        reasons = []
        pest_risk = "low"

        # Rain washes away pesticides
        if rainfall >= self.LIGHT_RAIN:
            suitable = False
            reasons.append(f"Rain expected ({rainfall:.1f}mm) - pesticides will wash off")

        # High humidity increases pest risk
        if humidity > 80:
            pest_risk = "high"
            reasons.append("High humidity increases pest and disease risk")

        # Warm, humid conditions favor pests
        if temperature > 25 and humidity > 70:
            pest_risk = "high"
            reasons.append("Warm and humid - ideal conditions for pests")

        # Cold weather reduces pest activity
        if temperature < 15:
            pest_risk = "low"
            reasons.append("Cool weather - low pest activity")

        if suitable and pest_risk == "high":
            recommendation = "Good day for pest control application - high pest risk"
        elif suitable and pest_risk == "low":
            recommendation = "Pest control can be applied if needed - low pest risk"
        else:
            recommendation = "Avoid pest control application - " + "; ".join(reasons)

        return {
            "suitable": suitable,
            "pest_risk": pest_risk,
            "recommendation": recommendation,
            "reasons": reasons,
        }

    def _get_general_care_recommendation(
        self, rainfall: float, temp_max: float, temp_min: float, humidity: int, growth_stage: str
    ) -> str:
        """Get general crop care recommendation"""
        recommendations = []

        # Heavy rain recommendations
        if rainfall >= self.HEAVY_RAIN:
            recommendations.append("Ensure proper drainage to prevent waterlogging")
            recommendations.append("Check for signs of fungal diseases after rain")

        # Extreme heat recommendations
        if temp_max > 38:
            recommendations.append("Increase irrigation frequency")
            recommendations.append("Consider mulching to retain soil moisture")
            if growth_stage == "flowering":
                recommendations.append("Monitor for heat stress - critical stage")

        # Cold weather recommendations
        if temp_min < 10:
            recommendations.append("Protect sensitive crops from cold damage")
            recommendations.append("Delay irrigation until temperatures rise")

        # High humidity recommendations
        if humidity > 85:
            recommendations.append("Monitor for fungal diseases")
            recommendations.append("Ensure good air circulation")

        # Dry conditions recommendations
        if rainfall < 1 and humidity < 50:
            recommendations.append("Monitor soil moisture levels")
            recommendations.append("Irrigate as needed based on crop requirements")

        if not recommendations:
            recommendations.append("Normal conditions - continue regular care routine")

        return " | ".join(recommendations)

    def _generate_crop_care_summary(
        self,
        care_recommendations: List[Dict[str, Any]],
        optimal_fertilizer_days: List[date],
        optimal_pest_control_days: List[date],
    ) -> str:
        """Generate crop care summary"""
        total_days = len(care_recommendations)

        summary = f"Crop care plan for next {total_days} days: "

        if optimal_fertilizer_days:
            fert_dates = ", ".join([d.strftime("%b %d") for d in optimal_fertilizer_days[:3]])
            summary += f"Fertilizer application recommended on {len(optimal_fertilizer_days)} days ({fert_dates}). "
        else:
            summary += "No optimal days for fertilizer application in forecast. "

        if optimal_pest_control_days:
            pest_dates = ", ".join([d.strftime("%b %d") for d in optimal_pest_control_days[:3]])
            summary += (
                f"Pest control suitable on {len(optimal_pest_control_days)} days ({pest_dates}). "
            )
        else:
            summary += "No optimal days for pest control in forecast. "

        return summary


def get_weather_recommendations_service(
    db: AsyncSession, weather_service: WeatherService, severe_weather_service: SevereWeatherService
) -> WeatherRecommendationsService:
    """
    Factory function to create weather recommendations service instance

    Args:
        db: Database session
        weather_service: Weather service instance
        severe_weather_service: Severe weather service instance

    Returns:
        WeatherRecommendationsService instance
    """
    return WeatherRecommendationsService(
        db=db, weather_service=weather_service, severe_weather_service=severe_weather_service
    )
