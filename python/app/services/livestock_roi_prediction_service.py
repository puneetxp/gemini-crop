from __future__ import annotations

from app.core.crud_service import CrudService
from app.orm.livestock_roi_prediction import LivestockRoiPrediction


class LivestockRoiPredictionService(CrudService):
    model = LivestockRoiPrediction


# Singleton instance
_service = LivestockRoiPredictionService()


# Generic getter (for auto-generated routers)
def get_service() -> LivestockRoiPredictionService:
    """Get service instance (generic name for auto-generated code)"""
    return _service


# Specific getter (for manual/custom code compatibility)
def get_livestock_roi_prediction_service() -> LivestockRoiPredictionService:
    """Get service instance (specific name for backward compatibility)"""
    return _service
