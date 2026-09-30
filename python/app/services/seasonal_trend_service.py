from __future__ import annotations

from app.core.crud_service import CrudService
from app.orm.seasonal_trend import SeasonalTrend


class SeasonalTrendService(CrudService):
    model = SeasonalTrend


# Singleton instance
_service = SeasonalTrendService()


# Generic getter (for auto-generated routers)
def get_service() -> SeasonalTrendService:
    """Get service instance (generic name for auto-generated code)"""
    return _service


# Specific getter (for manual/custom code compatibility)
def get_seasonal_trend_service() -> SeasonalTrendService:
    """Get service instance (specific name for backward compatibility)"""
    return _service
