from __future__ import annotations

from app.core.crud_service import CrudService
from app.orm.crop_expense import CropExpense


class CropExpenseService(CrudService):
    model = CropExpense


# Singleton instance
_service = CropExpenseService()


# Generic getter (for auto-generated routers)
def get_service() -> CropExpenseService:
    """Get service instance (generic name for auto-generated code)"""
    return _service


# Specific getter (for manual/custom code compatibility)
def get_crop_expense_service() -> CropExpenseService:
    """Get service instance (specific name for backward compatibility)"""
    return _service
