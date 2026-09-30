"""
Severe Weather Monitoring Service
Implements severe weather detection, harvest window analysis, and emergency alerts

Task 23.2: Implement Severe Weather Monitoring
Validates: Requirements AC8 (Phase 6 - Required)
"""

import logging
from datetime import datetime, timedelta
from typing import TYPE_CHECKING
from typing import Any  # db kept for compatibility; queries use app.core.db.DB
from typing import Any as AsyncSession
from typing import Dict, List, Optional, Tuple

from app.services.farm_access import crop_for_user, farm_for_user, fetch_one
from app.services.weather_service import WeatherService

if TYPE_CHECKING:
    from app.orm.crop import Crop
    from app.orm.farm import Farm
    from app.orm.weather_alert import WeatherAlert

logger = logging.getLogger(__name__)


class SevereWeatherService:
    """
    Severe weather monitoring and alert system

    Features:
    - Severe weather detection (storms, cyclones, extreme temps, heavy rain)
    - Harvest window analysis (identify dry periods)
    - Emergency alert system (< 15 minute notification latency)
    - Microclimate predictions (farm-specific forecasts)
    """

    # Severe weather thresholds
    HEAVY_RAIN_THRESHOLD = 50.0  # mm per day
    EXTREME_TEMP_HIGH = 40.0  # °C
    EXTREME_TEMP_LOW = 5.0  # °C
    HIGH_WIND_SPEED = 15.0  # m/s (54 km/h)

    # Alert severity levels
    SEVERITY_LOW = "low"
    SEVERITY_MEDIUM = "medium"
    SEVERITY_HIGH = "high"
    SEVERITY_CRITICAL = "critical"

    # Alert types
    ALERT_HEAVY_RAIN = "heavy_rain"
    ALERT_EXTREME_HEAT = "extreme_heat"
    ALERT_EXTREME_COLD = "extreme_cold"
    ALERT_CYCLONE = "cyclone"
    ALERT_STORM = "storm"
    ALERT_EMERGENCY_HARVEST = "emergency_harvest"

    def __init__(self, db: AsyncSession, weather_service: WeatherService):
        """
        Initialize severe weather service

        Args:
            db: Database session
            weather_service: Weather service instance
        """
        self.db = db
        self.weather_service = weather_service

    async def detect_severe_weather(
        self,
        latitude: float,
        longitude: float,
        farm_id: Optional[int] = None,
        state: Optional[str] = None,
        district: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Detect severe weather conditions from forecast

        Args:
            latitude: GPS latitude
            longitude: GPS longitude
            farm_id: Farm ID (optional)
            state: State name (optional)
            district: District name (optional)

        Returns:
            List of severe weather alerts
        """
        alerts = []

        # Get 7-day forecast
        forecast_data = await self.weather_service.get_forecast(
            latitude, longitude, days=7, use_cache=True
        )

        if not forecast_data or not forecast_data.get("forecasts"):
            logger.warning("No forecast data available for severe weather detection")
            return alerts

        # Analyze each forecast day
        for forecast in forecast_data["forecasts"]:
            date = forecast["date"]

            # Check for heavy rain
            if forecast.get("rainfall", 0) >= self.HEAVY_RAIN_THRESHOLD:
                alerts.append(
                    {
                        "alert_type": self.ALERT_HEAVY_RAIN,
                        "severity": self._calculate_rain_severity(forecast["rainfall"]),
                        "date": date,
                        "rainfall": forecast["rainfall"],
                        "message": f"Heavy rainfall expected: {forecast['rainfall']:.1f}mm",
                        "recommendation": "Postpone irrigation, ensure drainage, protect crops from waterlogging",
                    }
                )

            # Check for extreme heat
            if forecast.get("temp_max", 0) >= self.EXTREME_TEMP_HIGH:
                alerts.append(
                    {
                        "alert_type": self.ALERT_EXTREME_HEAT,
                        "severity": self._calculate_heat_severity(forecast["temp_max"]),
                        "date": date,
                        "temperature": forecast["temp_max"],
                        "message": f"Extreme heat expected: {forecast['temp_max']:.1f}°C",
                        "recommendation": "Increase irrigation, provide shade for livestock, avoid midday field work",
                    }
                )

            # Check for extreme cold
            if forecast.get("temp_min", 100) <= self.EXTREME_TEMP_LOW:
                alerts.append(
                    {
                        "alert_type": self.ALERT_EXTREME_COLD,
                        "severity": self.SEVERITY_HIGH,
                        "date": date,
                        "temperature": forecast["temp_min"],
                        "message": f"Extreme cold expected: {forecast['temp_min']:.1f}°C",
                        "recommendation": "Protect sensitive crops, shelter livestock, cover young plants",
                    }
                )

            # Check for high winds (storm indicator)
            if forecast.get("wind_speed", 0) >= self.HIGH_WIND_SPEED:
                alerts.append(
                    {
                        "alert_type": self.ALERT_STORM,
                        "severity": self._calculate_wind_severity(forecast["wind_speed"]),
                        "date": date,
                        "wind_speed": forecast["wind_speed"],
                        "message": f"High winds expected: {forecast['wind_speed']:.1f}m/s",
                        "recommendation": "Secure loose items, protect tall crops, shelter livestock",
                    }
                )

        # Check for cyclone alerts from weather service
        weather_alerts = await self.weather_service.get_weather_alerts(
            latitude, longitude, state, district
        )

        for alert in weather_alerts:
            if "cyclone" in alert.get("event_type", "").lower():
                alerts.append(
                    {
                        "alert_type": self.ALERT_CYCLONE,
                        "severity": self.SEVERITY_CRITICAL,
                        "date": alert["start_time"],
                        "message": alert.get("headline", "Cyclone warning"),
                        "description": alert.get("description", ""),
                        "recommendation": "Emergency harvest if crops are ready, secure all assets, evacuate if necessary",
                    }
                )

        # Store alerts in database
        if alerts:
            await self._store_alerts(alerts, farm_id, state, district)

        return alerts

    async def analyze_harvest_windows(
        self, latitude: float, longitude: float, days_ahead: int = 14
    ) -> Dict[str, Any]:
        """
        Analyze weather forecast to identify optimal harvest windows

        Args:
            latitude: GPS latitude
            longitude: GPS longitude
            days_ahead: Number of days to analyze (default: 14)

        Returns:
            Harvest window analysis with dry periods
        """
        # Get extended forecast
        forecast_data = await self.weather_service.get_forecast(
            latitude, longitude, days=days_ahead, use_cache=True
        )

        if not forecast_data or not forecast_data.get("forecasts"):
            logger.warning("No forecast data available for harvest window analysis")
            return {}

        # Identify dry periods (consecutive days with < 5mm rain)
        dry_periods = []
        current_period = None

        for forecast in forecast_data["forecasts"]:
            date = forecast["date"]
            rainfall = forecast.get("rainfall", 0)

            if rainfall < 5.0:  # Dry day
                if current_period is None:
                    current_period = {
                        "start_date": date,
                        "end_date": date,
                        "days": 1,
                        "avg_temp": forecast.get("temp_max", 0),
                        "avg_humidity": forecast.get("humidity", 0),
                    }
                else:
                    current_period["end_date"] = date
                    current_period["days"] += 1
                    current_period["avg_temp"] = (
                        current_period["avg_temp"] + forecast.get("temp_max", 0)
                    ) / 2
                    current_period["avg_humidity"] = (
                        current_period["avg_humidity"] + forecast.get("humidity", 0)
                    ) / 2
            else:  # Rainy day
                if current_period and current_period["days"] >= 2:
                    dry_periods.append(current_period)
                current_period = None

        # Add final period if exists
        if current_period and current_period["days"] >= 2:
            dry_periods.append(current_period)

        # Rank harvest windows by suitability
        for period in dry_periods:
            period["suitability_score"] = self._calculate_harvest_suitability(period)

        dry_periods.sort(key=lambda x: x["suitability_score"], reverse=True)

        return {
            "latitude": latitude,
            "longitude": longitude,
            "forecast_days": days_ahead,
            "dry_periods": dry_periods,
            "optimal_window": dry_periods[0] if dry_periods else None,
            "recommendation": self._generate_harvest_recommendation(dry_periods),
        }

    async def check_emergency_harvest_alert(
        self,
        farm_id: int,
        crop_id: int,
        user=None,
    ) -> Optional[Dict[str, Any]]:
        """
        Check if emergency harvest is needed due to severe weather

        Args:
            farm_id: Farm ID
            crop_id: Crop ID

        Returns:
            Emergency harvest alert or None
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
                return None
            try:
                crop = crop_for_user(crop_id, None)
            except LookupError:
                crop = None

        if not crop:
            logger.error(f"Crop {crop_id} not found")
            return None
        # farms has location_state / location_district; crops has crop_name (no state/district/crop_type columns)
        farm.state = farm.get("location_state")
        farm.district = farm.get("location_district")
        crop.crop_type = crop.get("crop_name")

        # Get farm GPS coordinates
        latitude = float(farm.latitude) if hasattr(farm, "latitude") and farm.latitude else None
        longitude = float(farm.longitude) if hasattr(farm, "longitude") and farm.longitude else None

        if not latitude or not longitude:
            logger.warning(f"Farm {farm_id} has no GPS coordinates")
            return None

        # Detect severe weather
        severe_weather = await self.detect_severe_weather(
            latitude, longitude, farm_id, farm.state, farm.district
        )

        # Check if crop is near harvest and severe weather threatens it
        if crop.expected_harvest_date:
            days_to_harvest = (crop.expected_harvest_date - datetime.now().date()).days

            # If harvest is within 14 days and severe weather detected
            if 0 <= days_to_harvest <= 14 and severe_weather:
                critical_alerts = [
                    a
                    for a in severe_weather
                    if a["severity"] in [self.SEVERITY_HIGH, self.SEVERITY_CRITICAL]
                ]

                if critical_alerts:
                    # Analyze harvest windows
                    harvest_windows = await self.analyze_harvest_windows(
                        latitude, longitude, days_ahead=7
                    )

                    return {
                        "alert_type": self.ALERT_EMERGENCY_HARVEST,
                        "severity": self.SEVERITY_CRITICAL,
                        "farm_id": farm_id,
                        "crop_id": crop_id,
                        "crop_type": crop.crop_type,
                        "expected_harvest_date": crop.expected_harvest_date,
                        "days_to_harvest": days_to_harvest,
                        "severe_weather": critical_alerts,
                        "harvest_windows": harvest_windows,
                        "message": f"Emergency harvest recommended for {crop.crop_type}",
                        "recommendation": self._generate_emergency_harvest_recommendation(
                            days_to_harvest, critical_alerts, harvest_windows
                        ),
                    }

        return None

    async def get_microclimate_prediction(
        self,
        latitude: float,
        longitude: float,
        farm_characteristics: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Generate microclimate predictions for individual farm

        Args:
            latitude: GPS latitude
            longitude: GPS longitude
            farm_characteristics: Farm-specific characteristics (elevation, slope, etc.)

        Returns:
            Microclimate prediction with farm-specific adjustments
        """
        # Get base weather forecast
        forecast_data = await self.weather_service.get_forecast(
            latitude, longitude, days=7, use_cache=True
        )

        if not forecast_data or not forecast_data.get("forecasts"):
            logger.warning("No forecast data available for microclimate prediction")
            return {}

        # Apply farm-specific adjustments
        adjusted_forecasts = []
        for forecast in forecast_data["forecasts"]:
            adjusted = forecast.copy()

            # Apply microclimate adjustments based on farm characteristics
            if farm_characteristics:
                # Elevation adjustment (temp decreases ~0.6°C per 100m)
                if "elevation" in farm_characteristics:
                    elevation_m = farm_characteristics["elevation"]
                    temp_adjustment = -(elevation_m / 100) * 0.6
                    adjusted["temp_min"] = forecast.get("temp_min", 0) + temp_adjustment
                    adjusted["temp_max"] = forecast.get("temp_max", 0) + temp_adjustment

                # Slope adjustment (affects water retention)
                if "slope" in farm_characteristics:
                    slope = farm_characteristics["slope"]
                    if slope > 5:  # Steep slope
                        adjusted["effective_rainfall"] = forecast.get("rainfall", 0) * 0.8
                    else:
                        adjusted["effective_rainfall"] = forecast.get("rainfall", 0)

                # Soil type adjustment (affects moisture retention)
                if "soil_type" in farm_characteristics:
                    soil_type = farm_characteristics["soil_type"].lower()
                    if "sandy" in soil_type:
                        adjusted["irrigation_need"] = "high"
                    elif "clay" in soil_type:
                        adjusted["irrigation_need"] = "low"
                    else:
                        adjusted["irrigation_need"] = "medium"

            adjusted_forecasts.append(adjusted)

        return {
            "latitude": latitude,
            "longitude": longitude,
            "farm_characteristics": farm_characteristics,
            "base_forecast": forecast_data,
            "microclimate_forecast": adjusted_forecasts,
            "adjustments_applied": (
                list(farm_characteristics.keys()) if farm_characteristics else []
            ),
        }

    def _calculate_rain_severity(self, rainfall: float) -> str:
        """Calculate severity level for rainfall"""
        if rainfall >= 150:
            return self.SEVERITY_CRITICAL
        elif rainfall >= 100:
            return self.SEVERITY_HIGH
        elif rainfall >= 50:
            return self.SEVERITY_MEDIUM
        else:
            return self.SEVERITY_LOW

    def _calculate_heat_severity(self, temperature: float) -> str:
        """Calculate severity level for heat"""
        if temperature >= 45:
            return self.SEVERITY_CRITICAL
        elif temperature >= 42:
            return self.SEVERITY_HIGH
        elif temperature >= 40:
            return self.SEVERITY_MEDIUM
        else:
            return self.SEVERITY_LOW

    def _calculate_wind_severity(self, wind_speed: float) -> str:
        """Calculate severity level for wind"""
        if wind_speed >= 25:  # 90 km/h
            return self.SEVERITY_CRITICAL
        elif wind_speed >= 20:  # 72 km/h
            return self.SEVERITY_HIGH
        elif wind_speed >= 15:  # 54 km/h
            return self.SEVERITY_MEDIUM
        else:
            return self.SEVERITY_LOW

    def _calculate_harvest_suitability(self, period: Dict[str, Any]) -> float:
        """
        Calculate suitability score for harvest window

        Score based on:
        - Number of consecutive dry days (more is better)
        - Temperature (moderate is better)
        - Humidity (lower is better)
        """
        score = 0.0

        # Days score (max 50 points)
        days = period["days"]
        score += min(days * 10, 50)

        # Temperature score (max 30 points)
        temp = period["avg_temp"]
        if 20 <= temp <= 35:
            score += 30
        elif 15 <= temp < 20 or 35 < temp <= 38:
            score += 20
        else:
            score += 10

        # Humidity score (max 20 points)
        humidity = period["avg_humidity"]
        if humidity < 60:
            score += 20
        elif humidity < 70:
            score += 15
        elif humidity < 80:
            score += 10
        else:
            score += 5

        return score

    def _generate_harvest_recommendation(self, dry_periods: List[Dict[str, Any]]) -> str:
        """Generate harvest timing recommendation"""
        if not dry_periods:
            return "No suitable harvest windows found in forecast. Monitor weather closely."

        optimal = dry_periods[0]
        start = optimal["start_date"].strftime("%B %d")
        end = optimal["end_date"].strftime("%B %d")
        days = optimal["days"]

        return (
            f"Optimal harvest window: {start} to {end} ({days} consecutive dry days). "
            f"Temperature: {optimal['avg_temp']:.1f}°C, Humidity: {optimal['avg_humidity']:.0f}%. "
            f"Plan harvest operations during this period for best results."
        )

    def _generate_emergency_harvest_recommendation(
        self,
        days_to_harvest: int,
        severe_weather: List[Dict[str, Any]],
        harvest_windows: Dict[str, Any],
    ) -> str:
        """Generate emergency harvest recommendation"""
        weather_types = [a["alert_type"] for a in severe_weather]

        recommendation = f"URGENT: Severe weather approaching in {days_to_harvest} days. "

        if harvest_windows.get("optimal_window"):
            window = harvest_windows["optimal_window"]
            start = window["start_date"].strftime("%B %d")
            recommendation += f"Harvest immediately during {start} window before weather arrives. "
        else:
            recommendation += "Harvest immediately - no ideal windows available. "

        if self.ALERT_CYCLONE in weather_types:
            recommendation += "Cyclone warning - prioritize crop protection and safety. "
        elif self.ALERT_HEAVY_RAIN in weather_types:
            recommendation += "Heavy rain expected - harvest to prevent waterlogging damage. "
        elif self.ALERT_EXTREME_HEAT in weather_types:
            recommendation += "Extreme heat expected - harvest early morning or evening. "

        return recommendation

    async def _store_alerts(
        self,
        alerts: List[Dict[str, Any]],
        farm_id: Optional[int],
        state: Optional[str],
        district: Optional[str],
    ) -> None:
        """Store weather alerts in database"""
        try:
            for alert in alerts:
                alert_data = {
                    "farm_id": farm_id,
                    "state": state or "Unknown",
                    "district": district,
                    "alert_type": alert["alert_type"],
                    "severity": alert["severity"],
                    "message": alert["message"],
                    "recommendation": alert.get("recommendation"),
                    "valid_from": alert.get("date", datetime.now()),
                    "valid_until": alert.get("date", datetime.now()) + timedelta(days=1),
                    "is_active": 1,  # smallint column
                }

                # Insert alert (skip an identical alert that is already stored)
                exists = fetch_one(
                    """SELECT id FROM weather_alerts WHERE COALESCE(farm_id, 0) = ? AND alert_type = ?
                       AND valid_from = ? LIMIT 1""",
                    [farm_id or 0, alert_data["alert_type"], alert_data["valid_from"]],
                )
                if not exists:
                    cols = list(alert_data.keys())
                    fetch_one(
                        f"INSERT INTO weather_alerts ({', '.join(cols)}) VALUES ({', '.join('?' for _ in cols)}) RETURNING id",
                        [alert_data[c] for c in cols],
                    )

            logger.info(f"Stored {len(alerts)} weather alerts")

        except Exception as e:
            logger.error(f"Error storing weather alerts: {str(e)}")


def get_severe_weather_service(
    db: AsyncSession, weather_service: WeatherService
) -> SevereWeatherService:
    """
    Factory function to create severe weather service instance

    Args:
        db: Database session
        weather_service: Weather service instance

    Returns:
        SevereWeatherService instance
    """
    return SevereWeatherService(db=db, weather_service=weather_service)
