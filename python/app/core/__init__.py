"""CropSense AI Core Infrastructure Package."""
from __future__ import annotations

from app.core.config import settings
from app.core.crud_service import CrudService
from app.core.db import DB
from app.core.model import Model
from app.core.ownership import (
    OWNER_COLUMNS,
    OWNERSHIP,
    PARENTS,
    SHARED_READ,
    can_access,
    enforce_owner_columns,
    get_ownership_clause,
    is_shared_read,
    validate_parent_ownership,
)

__all__ = [
    "settings",
    "DB",
    "Model",
    "CrudService",
    "OWNERSHIP",
    "SHARED_READ",
    "OWNER_COLUMNS",
    "PARENTS",
    "get_ownership_clause",
    "is_shared_read",
    "enforce_owner_columns",
    "validate_parent_ownership",
    "can_access",
]
