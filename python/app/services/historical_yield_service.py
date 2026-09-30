from __future__ import annotations

from app.core.crud_service import CrudService
from app.orm.historical_yield import HistoricalYield


class HistoricalYieldService(CrudService):
    model = HistoricalYield


# Singleton instance
_service = HistoricalYieldService()


# Generic getter (for auto-generated routers)
def get_service() -> HistoricalYieldService:
    """Get service instance (generic name for auto-generated code)"""
    return _service


# Specific getter (for manual/custom code compatibility)
def get_historical_yield_service() -> HistoricalYieldService:
    """Get service instance (specific name for backward compatibility)"""
    return _service
