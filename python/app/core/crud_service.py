"""
Base CrudService implementation for CropSense AI services.
Integrates row-level ownership security, parent validation, and parameter sanitization.
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from app.core.db import DB
from app.core.ownership import (
    enforce_owner_columns,
    get_ownership_clause,
    is_shared_read,
    validate_parent_ownership,
)

logger = logging.getLogger("cropsense.crud_service")


class CrudService:
    """Base CRUD service providing secure data access and mutations."""

    model: Any = None
    table: str = ""

    def __init__(self, model_cls: Any = None, table: str = "") -> None:
        if model_cls is not None:
            self.model = model_cls
        if table:
            self.table = table
        elif self.model and hasattr(self.model, "table"):
            self.table = self.model.table

    def _get_owner_id(self, owner: Optional[Dict[str, Any]]) -> Optional[int]:
        """Extract verified user id from owner context."""
        if not owner:
            return None
        return owner.get("id")

    def all(
        self,
        owner: Optional[Dict[str, Any]] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """Retrieve all records with optional pagination and ownership scoping."""
        uid = self._get_owner_id(owner)
        sql = f"SELECT t.* FROM {self.table} t"
        params: Dict[str, Any] = {}

        # Apply ownership rule if owner specified and not shared read
        if uid is not None and not is_shared_read(self.table):
            clause = get_ownership_clause(self.table, uid, alias="t")
            if clause:
                sql += f" WHERE {clause}"

        sql += " ORDER BY t.id DESC"
        if limit is not None:
            sql += f" LIMIT {int(limit)}"
        if offset is not None:
            sql += f" OFFSET {int(offset)}"

        return DB.raw(sql, params).exe().rows

    def find(self, item_id: Any, owner: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        """Find a single record by primary key, verifying ownership."""
        uid = self._get_owner_id(owner)
        sql = f"SELECT t.* FROM {self.table} t WHERE t.id = %(id)s"
        params: Dict[str, Any] = {"id": item_id}

        if uid is not None and not is_shared_read(self.table):
            clause = get_ownership_clause(self.table, uid, alias="t")
            if clause:
                sql += f" AND {clause}"

        sql += " LIMIT 1"
        return DB.raw(sql, params).exe().first()

    def where(
        self,
        filters: Dict[str, Any],
        owner: Optional[Dict[str, Any]] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """Filter records by dictionary of column -> value."""
        uid = self._get_owner_id(owner)
        clauses = []
        params: Dict[str, Any] = {}

        for i, (col, val) in enumerate(filters.items()):
            p_name = f"w_{col}_{i}"
            clauses.append(f"t.{col} = %({p_name})s")
            params[p_name] = val

        where_str = " AND ".join(clauses) if clauses else "1=1"
        sql = f"SELECT t.* FROM {self.table} t WHERE {where_str}"

        if uid is not None and not is_shared_read(self.table):
            clause = get_ownership_clause(self.table, uid, alias="t")
            if clause:
                sql += f" AND {clause}"

        sql += " ORDER BY t.id DESC"
        if limit is not None:
            sql += f" LIMIT {int(limit)}"
        if offset is not None:
            sql += f" OFFSET {int(offset)}"

        return DB.raw(sql, params).exe().rows

    def create(self, data: Dict[str, Any], owner: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        """Insert record into database enforcing fillable, owner columns and parent checks."""
        uid = self._get_owner_id(owner)
        clean = dict(data)

        # Force owner column if user is signed in
        if uid is not None:
            clean = enforce_owner_columns(self.table, clean, uid)
            # Validate foreign key parent ownership
            if not validate_parent_ownership(self.table, clean, uid):
                logger.warning("Parent ownership validation failed for %s on table %s", clean, self.table)
                return None

        # Sanitize to fillable columns
        fillable = getattr(self.model, "fillable", [])
        if fillable:
            allowed = set(fillable) | {"enable", "created_at", "updated_at"}
            clean = {k: v for k, v in clean.items() if k in allowed and k != "id"}

        clean.setdefault("enable", 1)

        cols = list(clean.keys())
        placeholders = [f"%({col})s" for col in cols]
        sql = f"INSERT INTO {self.table} ({', '.join(cols)}) VALUES ({', '.join(placeholders)}) RETURNING *"

        res = DB.raw(sql, clean).exe()
        return res.first()

    def update(
        self,
        item_id: Any,
        data: Dict[str, Any],
        owner: Optional[Dict[str, Any]] = None,
    ) -> Optional[Dict[str, Any]]:
        """Update existing record enforcing ownership checks and column immutability."""
        existing = self.find(item_id, owner=owner)
        if not existing:
            return None

        clean = dict(data)
        # Strip immutable primary key and owner columns on update
        clean.pop("id", None)
        uid = self._get_owner_id(owner)
        if uid is not None:
            # Cannot modify owner columns
            from app.core.ownership import OWNER_COLUMNS
            owner_col = OWNER_COLUMNS.get(self.table)
            if owner_col:
                clean.pop(owner_col, None)

        fillable = getattr(self.model, "fillable", [])
        if fillable:
            clean = {k: v for k, v in clean.items() if k in fillable}

        if not clean:
            return existing

        set_clauses = [f"{col} = %({col})s" for col in clean.keys()]
        sql = f"UPDATE {self.table} SET {', '.join(set_clauses)}, updated_at = CURRENT_TIMESTAMP WHERE id = %(pk)s RETURNING *"
        params = {**clean, "pk": item_id}

        return DB.raw(sql, params).exe().first()

    def upsert(self, data: Dict[str, Any], owner: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        """Update if id present, otherwise create."""
        item_id = data.get("id")
        if item_id:
            return self.update(item_id, data, owner=owner)
        return self.create(data, owner=owner)

    def delete(self, item_id: Any, owner: Optional[Dict[str, Any]] = None) -> bool:
        """Delete record if accessible by owner."""
        existing = self.find(item_id, owner=owner)
        if not existing:
            return False

        sql = f"DELETE FROM {self.table} WHERE id = %(id)s"
        DB.raw(sql, {"id": item_id}).exe()
        return True
