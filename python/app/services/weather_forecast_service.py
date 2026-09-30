from __future__ import annotations

from app.core.crud_service import CrudService
from app.orm.weather_forecast import WeatherForecast


class WeatherForecastService(CrudService):
    model = WeatherForecast


# Singleton instance
_service = WeatherForecastService()


# Generic getter (for auto-generated routers)
def get_service() -> WeatherForecastService:
    """Get service instance (generic name for auto-generated code)"""
    return _service


# Specific getter (for manual/custom code compatibility)
def get_weather_forecast_service() -> WeatherForecastService:
    """Get service instance (specific name for backward compatibility)"""
    return _service
