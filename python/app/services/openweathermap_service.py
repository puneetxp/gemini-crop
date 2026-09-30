"""
OpenWeatherMap API Integration Service
Backup weather source for reliability

Task 23.1: Integrate with Weather APIs
"""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import httpx
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

logger = logging.getLogger(__name__)


class OpenWeatherMapService:
    """Service for OpenWeatherMap API integration"""

    # OpenWeatherMap API configuration
    OWM_API_BASE_URL = "https://api.openweathermap.org/data/2.5"
    OWM_API_KEY = None  # Would be loaded from environment variables

    # API timeouts
    CONNECT_TIMEOUT = 5.0  # seconds
    READ_TIMEOUT = 10.0  # seconds

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize OpenWeatherMap service

        Args:
            api_key: OpenWeatherMap API key (optional, can be set later)
        """
        self.api_key = api_key or self.OWM_API_KEY
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
        Get current weather data from OpenWeatherMap

        Args:
            latitude: GPS latitude
            longitude: GPS longitude

        Returns:
            Current weather data or None if unavailable
        """
        if not self.api_key:
            logger.warning("OpenWeatherMap API key not configured")
            return None

        try:
            url = f"{self.OWM_API_BASE_URL}/weather"
            params = {
                "lat": latitude,
                "lon": longitude,
                "appid": self.api_key,
                "units": "metric",  # Celsius
            }

            logger.info(f"Fetching current weather from OpenWeatherMap for {latitude}, {longitude}")
            response = await self.client.get(url, params=params)
            response.raise_for_status()

            data = await response.json()

            # Parse OpenWeatherMap response
            weather_data = self._parse_current_weather(data)
            return weather_data

        except httpx.HTTPStatusError as e:
            logger.error(
                f"OpenWeatherMap API HTTP error: {e.response.status_code} - {e.response.text}"
            )
            return None
        except httpx.TimeoutException:
            logger.error("OpenWeatherMap API request timeout")
            raise  # Let retry handle this
        except httpx.NetworkError:
            logger.error("OpenWeatherMap API network error")
            raise  # Let retry handle this
        except Exception as e:
            logger.error(f"Unexpected error fetching current weather from OpenWeatherMap: {str(e)}")
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
        Get weather forecast from OpenWeatherMap

        Args:
            latitude: GPS latitude
            longitude: GPS longitude
            days: Number of days to forecast (max 7 for free tier)

        Returns:
            Weather forecast data or None if unavailable
        """
        if not self.api_key:
            logger.warning("OpenWeatherMap API key not configured")
            return None

        # OpenWeatherMap free tier supports up to 5 days (40 3-hour forecasts)
        # For 7-14 day forecasts, would need One Call API 3.0 (paid)
        if days > 5:
            logger.warning(
                f"OpenWeatherMap free tier supports max 5 days. Using 5 days instead of {days}."
            )
            days = 5

        try:
            url = f"{self.OWM_API_BASE_URL}/forecast"
            params = {
                "lat": latitude,
                "lon": longitude,
                "appid": self.api_key,
                "units": "metric",  # Celsius
                "cnt": days * 8,  # 8 forecasts per day (3-hour intervals)
            }

            logger.info(
                f"Fetching {days}-day forecast from OpenWeatherMap for {latitude}, {longitude}"
            )
            response = await self.client.get(url, params=params)
            response.raise_for_status()

            data = await response.json()

            # Parse OpenWeatherMap forecast
            forecast_data = self._parse_forecast(data, days)
            return forecast_data

        except httpx.HTTPStatusError as e:
            logger.error(
                f"OpenWeatherMap API HTTP error: {e.response.status_code} - {e.response.text}"
            )
            return None
        except httpx.TimeoutException:
            logger.error("OpenWeatherMap API request timeout")
            raise  # Let retry handle this
        except httpx.NetworkError:
            logger.error("OpenWeatherMap API network error")
            raise  # Let retry handle this
        except Exception as e:
            logger.error(f"Unexpected error fetching forecast from OpenWeatherMap: {str(e)}")
            return None

    async def get_weather_alerts(self, latitude: float, longitude: float) -> List[Dict[str, Any]]:
        """
        Get weather alerts from OpenWeatherMap One Call API
        Note: Requires One Call API 3.0 subscription

        Args:
            latitude: GPS latitude
            longitude: GPS longitude

        Returns:
            List of weather alerts
        """
        if not self.api_key:
            logger.warning("OpenWeatherMap API key not configured")
            return []

        try:
            # One Call API 3.0 endpoint (requires subscription)
            url = f"https://api.openweathermap.org/data/3.0/onecall"
            params = {
                "lat": latitude,
                "lon": longitude,
                "appid": self.api_key,
                "exclude": "current,minutely,hourly,daily",  # Only get alerts
            }

            logger.info(f"Fetching weather alerts from OpenWeatherMap for {latitude}, {longitude}")
            response = await self.client.get(url, params=params)
            response.raise_for_status()

            data = await response.json()

            # Parse alerts
            alerts = self._parse_alerts(data.get("alerts", []))
            return alerts

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 401:
                logger.warning("OpenWeatherMap One Call API requires subscription")
            else:
                logger.error(
                    f"OpenWeatherMap API HTTP error: {e.response.status_code} - {e.response.text}"
                )
            return []
        except Exception as e:
            logger.error(f"Unexpected error fetching alerts from OpenWeatherMap: {str(e)}")
            return []

    def _parse_current_weather(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parse OpenWeatherMap current weather response

        Args:
            data: Raw OpenWeatherMap API response

        Returns:
            Standardized weather data
        """
        try:
            main = data.get("main", {})
            wind = data.get("wind", {})
            weather = data.get("weather", [{}])[0]
            rain = data.get("rain", {})

            return {
                "temperature": main.get("temp", 0.0),
                "feels_like": main.get("feels_like", 0.0),
                "humidity": main.get("humidity", 0),
                "pressure": main.get("pressure", 0),
                "wind_speed": wind.get("speed", 0.0),
                "wind_direction": wind.get("deg", 0),
                "rainfall": rain.get("1h", 0.0),  # Rainfall in last 1 hour
                "description": weather.get("description", ""),
                "timestamp": datetime.fromtimestamp(data.get("dt", datetime.now().timestamp())),
                "source": "OpenWeatherMap",
            }
        except Exception as e:
            logger.error(f"Error parsing OpenWeatherMap current weather: {str(e)}")
            return {}

    def _parse_forecast(self, data: Dict[str, Any], days: int) -> Dict[str, Any]:
        """
        Parse OpenWeatherMap forecast response

        Args:
            data: Raw OpenWeatherMap API response
            days: Number of forecast days

        Returns:
            Standardized forecast data
        """
        try:
            forecast_list = data.get("list", [])

            # Group 3-hour forecasts by day
            daily_forecasts = {}
            for forecast in forecast_list:
                dt = datetime.fromtimestamp(forecast.get("dt", 0))
                date_key = dt.date()

                if date_key not in daily_forecasts:
                    daily_forecasts[date_key] = {
                        "date": datetime.combine(date_key, datetime.min.time()),
                        "temps": [],
                        "humidity_values": [],
                        "rainfall_values": [],
                        "wind_speeds": [],
                        "descriptions": [],
                    }

                main = forecast.get("main", {})
                wind = forecast.get("wind", {})
                weather = forecast.get("weather", [{}])[0]
                rain = forecast.get("rain", {})

                daily_forecasts[date_key]["temps"].append(main.get("temp", 0.0))
                daily_forecasts[date_key]["humidity_values"].append(main.get("humidity", 0))
                daily_forecasts[date_key]["rainfall_values"].append(rain.get("3h", 0.0))
                daily_forecasts[date_key]["wind_speeds"].append(wind.get("speed", 0.0))
                daily_forecasts[date_key]["descriptions"].append(weather.get("description", ""))

            # Calculate daily aggregates
            aggregated_forecasts = []
            for date_key in sorted(daily_forecasts.keys())[:days]:
                day_data = daily_forecasts[date_key]
                temps = day_data["temps"]

                aggregated_forecasts.append(
                    {
                        "date": day_data["date"],
                        "temp_min": min(temps) if temps else 0.0,
                        "temp_max": max(temps) if temps else 0.0,
                        "humidity": (
                            int(sum(day_data["humidity_values"]) / len(day_data["humidity_values"]))
                            if day_data["humidity_values"]
                            else 0
                        ),
                        "rainfall": sum(day_data["rainfall_values"]),
                        "wind_speed": (
                            sum(day_data["wind_speeds"]) / len(day_data["wind_speeds"])
                            if day_data["wind_speeds"]
                            else 0.0
                        ),
                        "description": (
                            max(set(day_data["descriptions"]), key=day_data["descriptions"].count)
                            if day_data["descriptions"]
                            else ""
                        ),
                    }
                )

            return {
                "days": len(aggregated_forecasts),
                "forecasts": aggregated_forecasts,
                "source": "OpenWeatherMap",
                "retrieved_at": datetime.now(),
            }
        except Exception as e:
            logger.error(f"Error parsing OpenWeatherMap forecast: {str(e)}")
            return {"days": 0, "forecasts": [], "source": "OpenWeatherMap"}

    def _parse_alerts(self, alerts_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Parse OpenWeatherMap weather alerts

        Args:
            alerts_data: Raw alerts data from API

        Returns:
            List of standardized alert data
        """
        try:
            parsed_alerts = []
            for alert in alerts_data:
                # Map OpenWeatherMap severity to our standard
                severity_map = {
                    "Extreme": "critical",
                    "Severe": "high",
                    "Moderate": "medium",
                    "Minor": "low",
                }

                parsed_alerts.append(
                    {
                        "alert_id": alert.get("sender_name", ""),
                        "severity": severity_map.get(alert.get("severity", "Minor"), "low"),
                        "event_type": alert.get("event", ""),
                        "headline": alert.get("event", ""),
                        "description": alert.get("description", ""),
                        "start_time": datetime.fromtimestamp(
                            alert.get("start", datetime.now().timestamp())
                        ),
                        "end_time": datetime.fromtimestamp(
                            alert.get("end", datetime.now().timestamp())
                        ),
                        "affected_areas": [alert.get("sender_name", "")],
                        "source": "OpenWeatherMap",
                    }
                )

            return parsed_alerts
        except Exception as e:
            logger.error(f"Error parsing OpenWeatherMap alerts: {str(e)}")
            return []


def get_openweathermap_service(api_key: Optional[str] = None) -> OpenWeatherMapService:
    """
    Factory function to create OpenWeatherMap service instance

    Args:
        api_key: OpenWeatherMap API key (optional)

    Returns:
        OpenWeatherMapService instance
    """
    return OpenWeatherMapService(api_key=api_key)
