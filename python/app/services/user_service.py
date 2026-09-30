from __future__ import annotations

from app.core.crud_service import CrudService
from app.orm.user import User


class UserService(CrudService):
    model = User


# Singleton instance
_service = UserService()


# Generic getter (for auto-generated routers)
def get_service() -> UserService:
    """Get service instance (generic name for auto-generated code)"""
    return _service


# Specific getter (for manual/custom code compatibility)
def get_user_service() -> UserService:
    """Get service instance (specific name for backward compatibility)"""
    return _service
