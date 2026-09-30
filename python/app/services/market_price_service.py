from __future__ import annotations

from app.core.crud_service import CrudService
from app.orm.market_price import MarketPrice


class MarketPriceService(CrudService):
    model = MarketPrice


# Singleton instance
_service = MarketPriceService()


# Generic getter (for auto-generated routers)
def get_service() -> MarketPriceService:
    """Get service instance (generic name for auto-generated code)"""
    return _service


# Specific getter (for manual/custom code compatibility)
def get_market_price_service() -> MarketPriceService:
    """Get service instance (specific name for backward compatibility)"""
    return _service
