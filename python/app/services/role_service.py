from __future__ import annotations

from app.core.crud_service import CrudService
from app.orm.role import Role


class RoleService(CrudService):
    model = Role


# Singleton instance
_service = RoleService()


# Generic getter (for auto-generated routers)
def get_service() -> RoleService:
    """Get service instance (generic name for auto-generated code)"""
    return _service


# Specific getter (for manual/custom code compatibility)
def get_role_service() -> RoleService:
    """Get service instance (specific name for backward compatibility)"""
    return _service
