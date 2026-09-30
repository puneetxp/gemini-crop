from __future__ import annotations

from app.core.crud_service import CrudService
from app.orm.crop_market_data import CropMarketData


class CropMarketDataService(CrudService):
    model = CropMarketData


# Singleton instance
_service = CropMarketDataService()


# Generic getter (for auto-generated routers)
def get_service() -> CropMarketDataService:
    """Get service instance (generic name for auto-generated code)"""
    return _service


# Specific getter (for manual/custom code compatibility)
def get_crop_market_data_service() -> CropMarketDataService:
    """Get service instance (specific name for backward compatibility)"""
    return _service
