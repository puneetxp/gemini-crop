from __future__ import annotations

from app.core.crud_service import CrudService
from app.orm.price_prediction import PricePrediction


class PricePredictionService(CrudService):
    model = PricePrediction


# Singleton instance
_service = PricePredictionService()


# Generic getter (for auto-generated routers)
def get_service() -> PricePredictionService:
    """Get service instance (generic name for auto-generated code)"""
    return _service


# Specific getter (for manual/custom code compatibility)
def get_price_prediction_service() -> PricePredictionService:
    """Get service instance (specific name for backward compatibility)"""
    return _service
