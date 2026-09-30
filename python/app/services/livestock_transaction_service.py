from __future__ import annotations

from app.core.crud_service import CrudService
from app.orm.livestock_transaction import LivestockTransaction


class LivestockTransactionService(CrudService):
    model = LivestockTransaction


# Singleton instance
_service = LivestockTransactionService()


# Generic getter (for auto-generated routers)
def get_service() -> LivestockTransactionService:
    """Get service instance (generic name for auto-generated code)"""
    return _service


# Specific getter (for manual/custom code compatibility)
def get_livestock_transaction_service() -> LivestockTransactionService:
    """Get service instance (specific name for backward compatibility)"""
    return _service
