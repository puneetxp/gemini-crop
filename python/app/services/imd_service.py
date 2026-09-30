"""
IMD (India Meteorological Department) API Integration Service
Handles real-time weather data retrieval from IMD

Task 23.1: Integrate with Weather APIs
"""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import httpx
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

logger = logging.getLogger(__name__)


class IMDService:
    """Service for IMD weather API integration"""

    # IMD API configuration
    # Note: These are placeholder URLs - actual IMD API endpoints would be configured
    IMD_API_BASE_URL = "https://api.imd.gov.in/v1"  # Placeholder
    IMD_API_KEY = None  # Would be loaded from environment variables

    # API timeouts
    CONNECT_TIMEOUT = 5.0  # seconds
    READ_TIMEOUT = 10.0  # seconds

    # Rate limiting
    MAX_REQUESTS_PER_MINUTE = 60

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize IMD service

        Args:
            api_key: IMD API key (optional, can be set later)
        """
        self.api_key = api_key or self.IMD_API_KEY
        self.client = httpx.AsyncClient(
            timeout=httpx.Timeout(timeout=self.READ_TIMEOUT, connect=self.CONNECT_TIMEOUT)
        )

    async def close(self):
        """Close HTTP client"""
        await self.client.aclose()

    async def __aenter__(self):
        """Async context manager entry"""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.close()
        return False

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((httpx.TimeoutException, httpx.NetworkError)),
    )
    async def get_current_weather(
        self, latitude: float, longitude: float
    ) -> Optional[Dict[str, Any]]:
        """
        Get current weather data from IMD

        Args:
            latitude: GPS latitude
            longitude: GPS longitude

        Returns:
            Current weather data or None if unavailable
        """
        if not self.api_key:
            logger.warning("IMD API key not configured")
            return None

        try:
            url = f"{self.IMD_API_BASE_URL}/weather/current"
            params = {"lat": latitude, "lon": longitude, "api_key": self.api_key}

            logger.info(f"Fetching current weather from IMD for {latitude}, {longitude}")
            response = await self.client.get(url, params=params)
            response.raise_for_status()

            data = await response.json()

            # Parse IMD response format
            weather_data = self._parse_current_weather(data)
            return weather_data

        except httpx.HTTPStatusError as e:
            logger.error(f"IMD API HTTP error: {e.response.status_code} - {e.response.text}")
            return None
        except httpx.TimeoutException:
            logger.error("IMD API request timeout")
            raise  # Let retry handle this
        except httpx.NetworkError:
            logger.error("IMD API network error")
            raise  # Let retry handle this
        except Exception as e:
            logger.error(f"Unexpected error fetching current weather from IMD: {str(e)}")
            return None

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((httpx.TimeoutException, httpx.NetworkError)),
    )
    async def get_forecast(
        self, latitude: float, longitude: float, days: int = 7
    ) -> Optional[Dict[str, Any]]:
        """
        Get weather forecast from IMD

        Args:
            latitude: GPS latitude
            longitude: GPS longitude
            days: Number of days to forecast (7 or 14)

        Returns:
            Weather forecast data or None if unavailable
        """
        if not self.api_key:
            logger.warning("IMD API key not configured")
            return None

        if days not in [7, 14]:
            logger.warning(f"Invalid forecast days: {days}. Using 7 days.")
            days = 7

        try:
            url = f"{self.IMD_API_BASE_URL}/weather/forecast"
            params = {"lat": latitude, "lon": longitude, "days": days, "api_key": self.api_key}

            logger.info(f"Fetching {days}-day forecast from IMD for {latitude}, {longitude}")
            response = await self.client.get(url, params=params)
            response.raise_for_status()

            data = await response.json()

            # Parse IMD forecast format
            forecast_data = self._parse_forecast(data, days)
            return forecast_data

        except httpx.HTTPStatusError as e:
            logger.error(f"IMD API HTTP error: {e.response.status_code} - {e.response.text}")
            return None
        except httpx.TimeoutException:
            logger.error("IMD API request timeout")
            raise  # Let retry handle this
        except httpx.NetworkError:
            logger.error("IMD API network error")
            raise  # Let retry handle this
        except Exception as e:
            logger.error(f"Unexpected error fetching forecast from IMD: {str(e)}")
            return None

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((httpx.TimeoutException, httpx.NetworkError)),
    )
    async def get_weather_alerts(
        self, state: str, district: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get weather alerts from IMD for a specific region

        Args:
            state: State name
            district: District name (optional)

        Returns:
            List of weather alerts
        """
        if not self.api_key:
            logger.warning("IMD API key not configured")
            return []

        try:
            url = f"{self.IMD_API_BASE_URL}/alerts"
            params = {"state": state, "api_key": self.api_key}

            if district:
                params["district"] = district

            logger.info(
                f"Fetching weather alerts from IMD for {state}, {district or 'all districts'}"
            )
            response = await self.client.get(url, params=params)
            response.raise_for_status()

            data = await response.json()

            # Parse IMD alerts format
            alerts = self._parse_alerts(data)
            return alerts

        except httpx.HTTPStatusError as e:
            logger.error(f"IMD API HTTP error: {e.response.status_code} - {e.response.text}")
            return []
        except httpx.TimeoutException:
            logger.error("IMD API request timeout")
            raise  # Let retry handle this
        except httpx.NetworkError:
            logger.error("IMD API network error")
            raise  # Let retry handle this
        except Exception as e:
            logger.error(f"Unexpected error fetching alerts from IMD: {str(e)}")
            return []

    async def get_historical_weather(
        self, latitude: float, longitude: float, start_date: datetime, end_date: datetime
    ) -> Optional[List[Dict[str, Any]]]:
        """
        Get historical weather data from IMD

        Args:
            latitude: GPS latitude
            longitude: GPS longitude
            start_date: Start date for historical data
            end_date: End date for historical data

        Returns:
            List of historical weather records or None
        """
        if not self.api_key:
            logger.warning("IMD API key not configured")
            return None

        try:
            url = f"{self.IMD_API_BASE_URL}/weather/historical"
            params = {
                "lat": latitude,
                "lon": longitude,
                "start_date": start_date.strftime("%Y-%m-%d"),
                "end_date": end_date.strftime("%Y-%m-%d"),
                "api_key": self.api_key,
            }

            logger.info(f"Fetching historical weather from IMD for {latitude}, {longitude}")
            response = await self.client.get(url, params=params)
            response.raise_for_status()

            data = await response.json()

            # Parse IMD historical data format
            historical_data = self._parse_historical_weather(data)
            return historical_data

        except httpx.HTTPStatusError as e:
            logger.error(f"IMD API HTTP error: {e.response.status_code} - {e.response.text}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error fetching historical weather from IMD: {str(e)}")
            return None

    def _parse_current_weather(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parse IMD current weather response

        Args:
            data: Raw IMD API response

        Returns:
            Standardized weather data
        """
        # This is a placeholder - actual parsing would depend on IMD API format
        try:
            return {
                "temperature": data.get("temp", 0.0),
                "feels_like": data.get("feels_like", 0.0),
                "humidity": data.get("humidity", 0),
                "pressure": data.get("pressure", 0),
                "wind_speed": data.get("wind_speed", 0.0),
                "wind_direction": data.get("wind_direction", 0),
                "rainfall": data.get("rainfall", 0.0),
                "description": data.get("description", ""),
                "timestamp": datetime.fromisoformat(
                    data.get("timestamp", datetime.now().isoformat())
                ),
                "source": "IMD",
            }
        except Exception as e:
            logger.error(f"Error parsing IMD current weather: {str(e)}")
            return {}

    def _parse_forecast(self, data: Dict[str, Any], days: int) -> Dict[str, Any]:
        """
        Parse IMD forecast response

        Args:
            data: Raw IMD API response
            days: Number of forecast days

        Returns:
            Standardized forecast data
        """
        # This is a placeholder - actual parsing would depend on IMD API format
        try:
            forecast_list = data.get("forecast", [])

            daily_forecasts = []
            for forecast in forecast_list[:days]:
                daily_forecasts.append(
                    {
                        "date": datetime.fromisoformat(
                            forecast.get("date", datetime.now().isoformat())
                        ),
                        "temp_min": forecast.get("temp_min", 0.0),
                        "temp_max": forecast.get("temp_max", 0.0),
                        "humidity": forecast.get("humidity", 0),
                        "rainfall": forecast.get("rainfall", 0.0),
                        "wind_speed": forecast.get("wind_speed", 0.0),
                        "description": forecast.get("description", ""),
                    }
                )

            return {
                "days": days,
                "forecasts": daily_forecasts,
                "source": "IMD",
                "retrieved_at": datetime.now(),
            }
        except Exception as e:
            logger.error(f"Error parsing IMD forecast: {str(e)}")
            return {"days": days, "forecasts": [], "source": "IMD"}

    def _parse_alerts(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Parse IMD weather alerts response

        Args:
            data: Raw IMD API response

        Returns:
            List of standardized alert data
        """
        # This is a placeholder - actual parsing would depend on IMD API format
        try:
            alerts_list = data.get("alerts", [])

            parsed_alerts = []
            for alert in alerts_list:
                parsed_alerts.append(
                    {
                        "alert_id": alert.get("id", ""),
                        "severity": alert.get("severity", "low"),  # low, medium, high, critical
                        "event_type": alert.get(
                            "event_type", ""
                        ),  # heavy_rain, cyclone, heatwave, etc.
                        "headline": alert.get("headline", ""),
                        "description": alert.get("description", ""),
                        "start_time": datetime.fromisoformat(
                            alert.get("start_time", datetime.now().isoformat())
                        ),
                        "end_time": datetime.fromisoformat(
                            alert.get("end_time", datetime.now().isoformat())
                        ),
                        "affected_areas": alert.get("affected_areas", []),
                        "source": "IMD",
                    }
                )

            return parsed_alerts
        except Exception as e:
            logger.error(f"Error parsing IMD alerts: {str(e)}")
            return []

    def _parse_historical_weather(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Parse IMD historical weather response

        Args:
            data: Raw IMD API response

        Returns:
            List of historical weather records
        """
        # This is a placeholder - actual parsing would depend on IMD API format
        try:
            records = data.get("records", [])

            parsed_records = []
            for record in records:
                parsed_records.append(
                    {
                        "date": datetime.fromisoformat(
                            record.get("date", datetime.now().isoformat())
                        ),
                        "temp_min": record.get("temp_min", 0.0),
                        "temp_max": record.get("temp_max", 0.0),
                        "temp_avg": record.get("temp_avg", 0.0),
                        "humidity": record.get("humidity", 0),
                        "rainfall": record.get("rainfall", 0.0),
                        "wind_speed": record.get("wind_speed", 0.0),
                        "source": "IMD",
                    }
                )

            return parsed_records
        except Exception as e:
            logger.error(f"Error parsing IMD historical weather: {str(e)}")
            return []


def get_imd_service(api_key: Optional[str] = None) -> IMDService:
    """
    Factory function to create IMD service instance

    Args:
        api_key: IMD API key (optional)

    Returns:
        IMDService instance
    """
    return IMDService(api_key=api_key)
