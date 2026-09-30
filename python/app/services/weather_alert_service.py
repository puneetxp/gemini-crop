from __future__ import annotations

from app.core.crud_service import CrudService
from app.orm.weather_alert import WeatherAlert


class WeatherAlertService(CrudService):
    model = WeatherAlert


# Singleton instance
_service = WeatherAlertService()


# Generic getter (for auto-generated routers)
def get_service() -> WeatherAlertService:
    """Get service instance (generic name for auto-generated code)"""
    return _service


# Specific getter (for manual/custom code compatibility)
def get_weather_alert_service() -> WeatherAlertService:
    """Get service instance (specific name for backward compatibility)"""
    return _service
