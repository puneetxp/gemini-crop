"""
Unified Weather Service with Failover Logic
Integrates IMD and OpenWeatherMap with automatic failover

Task 23.1: Integrate with Weather APIs
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from sqlalchemy import and_, desc, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.cache import TTL_SHORT, CacheManager
from app.services.imd_service import IMDService
from app.services.openweathermap_service import OpenWeatherMapService

logger = logging.getLogger(__name__)


class WeatherService:
    """
    Unified weather service with automatic failover
    Primary: IMD, Backup: OpenWeatherMap
    """

    # Cache TTL: 1 hour for forecasts
    FORECAST_CACHE_TTL = 3600  # 1 hour

    # Failover timeout: 5 seconds
    FAILOVER_TIMEOUT = 5.0

    def __init__(
        self,
        db: AsyncSession,
        imd_api_key: Optional[str] = None,
        owm_api_key: Optional[str] = None,
        cache_manager: Optional[CacheManager] = None,
    ):
        """
        Initialize unified weather service

        Args:
            db: Database session
            imd_api_key: IMD API key (optional)
            owm_api_key: OpenWeatherMap API key (optional)
            cache_manager: Cache manager instance (optional)
        """
        self.db = db
        self.imd_service = IMDService(api_key=imd_api_key)
        self.owm_service = OpenWeatherMapService(api_key=owm_api_key)
        self.cache_manager = cache_manager

    async def close(self):
        """Close all HTTP clients"""
        await self.imd_service.close()
        await self.owm_service.close()

    async def __aenter__(self):
        """Async context manager entry"""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.close()
        return False

    async def get_current_weather(
        self, latitude: float, longitude: float, use_cache: bool = True
    ) -> Optional[Dict[str, Any]]:
        """
        Get current weather with automatic failover

        Args:
            latitude: GPS latitude
            longitude: GPS longitude
            use_cache: Whether to use cached data

        Returns:
            Current weather data or None
        """
        # Check cache first
        if use_cache and self.cache_manager:
            cache_key = f"weather:current:{latitude}:{longitude}"
            cached_data = self.cache_manager.get(cache_key)
            if cached_data:
                logger.info("Returning cached current weather")
                return cached_data

        # Try IMD first
        logger.info("Fetching current weather from IMD (primary)")
        try:
            weather_data = await asyncio.wait_for(
                self.imd_service.get_current_weather(latitude, longitude),
                timeout=self.FAILOVER_TIMEOUT,
            )

            if weather_data:
                # Cache the result
                if self.cache_manager:
                    cache_key = f"weather:current:{latitude}:{longitude}"
                    self.cache_manager.set(cache_key, weather_data, ttl=TTL_SHORT)

                return weather_data
        except asyncio.TimeoutError:
            logger.warning("IMD API timeout, failing over to OpenWeatherMap")
        except Exception as e:
            logger.warning(f"IMD API error: {str(e)}, failing over to OpenWeatherMap")

        # Failover to OpenWeatherMap
        logger.info("Fetching current weather from OpenWeatherMap (backup)")
        try:
            weather_data = await self.owm_service.get_current_weather(latitude, longitude)

            if weather_data:
                # Cache the result
                if self.cache_manager:
                    cache_key = f"weather:current:{latitude}:{longitude}"
                    self.cache_manager.set(cache_key, weather_data, ttl=TTL_SHORT)

                return weather_data
        except Exception as e:
            logger.error(f"OpenWeatherMap API error: {str(e)}")

        logger.error("All weather sources failed")
        return None

    async def get_forecast(
        self, latitude: float, longitude: float, days: int = 7, use_cache: bool = True
    ) -> Optional[Dict[str, Any]]:
        """
        Get weather forecast with automatic failover

        Args:
            latitude: GPS latitude
            longitude: GPS longitude
            days: Number of days to forecast (7 or 14)
            use_cache: Whether to use cached data

        Returns:
            Weather forecast data or None
        """
        # Check cache first
        if use_cache and self.cache_manager:
            cache_key = f"weather:forecast:{latitude}:{longitude}:{days}"
            cached_data = self.cache_manager.get(cache_key)
            if cached_data:
                logger.info("Returning cached weather forecast")
                return cached_data

        # Try IMD first
        logger.info(f"Fetching {days}-day forecast from IMD (primary)")
        try:
            forecast_data = await asyncio.wait_for(
                self.imd_service.get_forecast(latitude, longitude, days),
                timeout=self.FAILOVER_TIMEOUT,
            )

            if forecast_data and forecast_data.get("forecasts"):
                # Store in database for historical analysis
                await self._store_forecast(latitude, longitude, forecast_data)

                # Cache the result
                if self.cache_manager:
                    cache_key = f"weather:forecast:{latitude}:{longitude}:{days}"
                    self.cache_manager.set(cache_key, forecast_data, ttl=self.FORECAST_CACHE_TTL)

                return forecast_data
        except asyncio.TimeoutError:
            logger.warning("IMD API timeout, failing over to OpenWeatherMap")
        except Exception as e:
            logger.warning(f"IMD API error: {str(e)}, failing over to OpenWeatherMap")

        # Failover to OpenWeatherMap
        logger.info(f"Fetching {days}-day forecast from OpenWeatherMap (backup)")
        try:
            # OpenWeatherMap free tier supports max 5 days
            adjusted_days = min(days, 5)
            forecast_data = await self.owm_service.get_forecast(latitude, longitude, adjusted_days)

            if forecast_data and forecast_data.get("forecasts"):
                # Store in database for historical analysis
                await self._store_forecast(latitude, longitude, forecast_data)

                # Cache the result
                if self.cache_manager:
                    cache_key = f"weather:forecast:{latitude}:{longitude}:{adjusted_days}"
                    self.cache_manager.set(cache_key, forecast_data, ttl=self.FORECAST_CACHE_TTL)

                return forecast_data
        except Exception as e:
            logger.error(f"OpenWeatherMap API error: {str(e)}")

        logger.error("All weather sources failed for forecast")
        return None

    async def get_weather_alerts(
        self,
        latitude: Optional[float] = None,
        longitude: Optional[float] = None,
        state: Optional[str] = None,
        district: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get weather alerts with automatic failover

        Args:
            latitude: GPS latitude (optional)
            longitude: GPS longitude (optional)
            state: State name (optional, for IMD)
            district: District name (optional, for IMD)

        Returns:
            List of weather alerts
        """
        alerts = []

        # Try IMD first (supports state/district lookup)
        if state:
            logger.info(
                f"Fetching weather alerts from IMD for {state}, {district or 'all districts'}"
            )
            try:
                imd_alerts = await asyncio.wait_for(
                    self.imd_service.get_weather_alerts(state, district),
                    timeout=self.FAILOVER_TIMEOUT,
                )
                alerts.extend(imd_alerts)
            except asyncio.TimeoutError:
                logger.warning("IMD alerts API timeout")
            except Exception as e:
                logger.warning(f"IMD alerts API error: {str(e)}")

        # Try OpenWeatherMap if we have GPS coordinates
        if latitude and longitude and not alerts:
            logger.info(f"Fetching weather alerts from OpenWeatherMap for {latitude}, {longitude}")
            try:
                owm_alerts = await self.owm_service.get_weather_alerts(latitude, longitude)
                alerts.extend(owm_alerts)
            except Exception as e:
                logger.warning(f"OpenWeatherMap alerts API error: {str(e)}")

        return alerts

    async def get_historical_weather(
        self, latitude: float, longitude: float, start_date: datetime, end_date: datetime
    ) -> Optional[List[Dict[str, Any]]]:
        """
        Get historical weather data

        Args:
            latitude: GPS latitude
            longitude: GPS longitude
            start_date: Start date
            end_date: End date

        Returns:
            List of historical weather records or None
        """
        # Try to get from database first
        stored_data = await self._get_stored_historical_weather(
            latitude, longitude, start_date, end_date
        )

        if stored_data:
            logger.info("Returning stored historical weather data")
            return stored_data

        # Try IMD API
        logger.info("Fetching historical weather from IMD")
        try:
            historical_data = await self.imd_service.get_historical_weather(
                latitude, longitude, start_date, end_date
            )

            if historical_data:
                # Store for future use
                await self._store_historical_weather(latitude, longitude, historical_data)
                return historical_data
        except Exception as e:
            logger.error(f"Error fetching historical weather from IMD: {str(e)}")

        return None

    async def analyze_seasonal_patterns(
        self, latitude: float, longitude: float, years: int = 3
    ) -> Dict[str, Any]:
        """
        Analyze seasonal weather patterns from historical data

        Args:
            latitude: GPS latitude
            longitude: GPS longitude
            years: Number of years to analyze

        Returns:
            Seasonal pattern analysis
        """
        end_date = datetime.now()
        start_date = end_date - timedelta(days=years * 365)

        historical_data = await self.get_historical_weather(
            latitude, longitude, start_date, end_date
        )

        if not historical_data:
            logger.warning("No historical data available for seasonal analysis")
            return {}

        # Analyze patterns by month
        monthly_patterns = {}
        for record in historical_data:
            month = record["date"].month
            if month not in monthly_patterns:
                monthly_patterns[month] = {"temps": [], "rainfall": [], "humidity": []}

            monthly_patterns[month]["temps"].append(record.get("temp_avg", 0.0))
            monthly_patterns[month]["rainfall"].append(record.get("rainfall", 0.0))
            monthly_patterns[month]["humidity"].append(record.get("humidity", 0))

        # Calculate averages
        seasonal_analysis = {}
        for month, data in monthly_patterns.items():
            seasonal_analysis[month] = {
                "avg_temp": sum(data["temps"]) / len(data["temps"]) if data["temps"] else 0.0,
                "avg_rainfall": (
                    sum(data["rainfall"]) / len(data["rainfall"]) if data["rainfall"] else 0.0
                ),
                "avg_humidity": (
                    sum(data["humidity"]) / len(data["humidity"]) if data["humidity"] else 0
                ),
                "monsoon_month": (
                    sum(data["rainfall"]) / len(data["rainfall"]) > 100
                    if data["rainfall"]
                    else False
                ),
            }

        return {
            "latitude": latitude,
            "longitude": longitude,
            "years_analyzed": years,
            "monthly_patterns": seasonal_analysis,
            "monsoon_months": [m for m, d in seasonal_analysis.items() if d["monsoon_month"]],
        }

    async def _store_forecast(
        self, latitude: float, longitude: float, forecast_data: Dict[str, Any]
    ) -> None:
        """
        Store forecast data in database for historical analysis

        Args:
            latitude: GPS latitude
            longitude: GPS longitude
            forecast_data: Forecast data to store
        """
        try:
            # This would store in a weather_forecasts table
            # Implementation depends on database schema
            logger.info(f"Storing forecast data for {latitude}, {longitude}")
            # TODO: Implement database storage
        except Exception as e:
            logger.error(f"Error storing forecast data: {str(e)}")

    async def _store_historical_weather(
        self, latitude: float, longitude: float, historical_data: List[Dict[str, Any]]
    ) -> None:
        """
        Store historical weather data in database

        Args:
            latitude: GPS latitude
            longitude: GPS longitude
            historical_data: Historical weather records
        """
        try:
            # This would store in a weather_history table
            # Implementation depends on database schema
            logger.info(f"Storing {len(historical_data)} historical weather records")
            # TODO: Implement database storage
        except Exception as e:
            logger.error(f"Error storing historical weather data: {str(e)}")

    async def _get_stored_historical_weather(
        self, latitude: float, longitude: float, start_date: datetime, end_date: datetime
    ) -> Optional[List[Dict[str, Any]]]:
        """
        Retrieve stored historical weather data from database

        Args:
            latitude: GPS latitude
            longitude: GPS longitude
            start_date: Start date
            end_date: End date

        Returns:
            List of historical weather records or None
        """
        try:
            # This would query a weather_history table
            # Implementation depends on database schema
            logger.info(f"Retrieving stored historical weather for {latitude}, {longitude}")
            # TODO: Implement database retrieval
            return None
        except Exception as e:
            logger.error(f"Error retrieving stored historical weather: {str(e)}")
            return None


def get_weather_service(
    db: AsyncSession,
    imd_api_key: Optional[str] = None,
    owm_api_key: Optional[str] = None,
    cache_manager: Optional[CacheManager] = None,
) -> WeatherService:
    """
    Factory function to create weather service instance

    Args:
        db: Database session
        imd_api_key: IMD API key (optional)
        owm_api_key: OpenWeatherMap API key (optional)
        cache_manager: Cache manager instance (optional)

    Returns:
        WeatherService instance
    """
    from app.core.config import get_system_setting

    resolved_imd = imd_api_key or get_system_setting("IMD_API_KEY")
    resolved_owm = owm_api_key or get_system_setting("OPENWEATHER_API_KEY")

    return WeatherService(
        db=db, imd_api_key=resolved_imd, owm_api_key=resolved_owm, cache_manager=cache_manager
    )
