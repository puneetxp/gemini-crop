from __future__ import annotations

from app.core.crud_service import CrudService
from app.orm.active_role import ActiveRole


class ActiveRoleService(CrudService):
    model = ActiveRole


# Singleton instance
_service = ActiveRoleService()


# Generic getter (for auto-generated routers)
def get_service() -> ActiveRoleService:
    """Get service instance (generic name for auto-generated code)"""
    return _service


# Specific getter (for manual/custom code compatibility)
def get_active_role_service() -> ActiveRoleService:
    """Get service instance (specific name for backward compatibility)"""
    return _service
