"""
Livestock data access for the custom /api/v1/livestock router (portfolio, ROI).

The router was written for an older LivestockService(db) with get_by_id/list/...;
the generator has since replaced livestock_service.py with the generic
CrudService, so every /api/v1/livestock call failed ("LivestockService() takes
no arguments"). This adapter gives the router the API it expects on top of the
generated service, scoped to the signed-in farmer (admins see everything).

Kept out of livestock_service.py because the generator overwrites that file.
"""

from typing import Any, Dict, List, Optional

from app.core.db import DB
from app.services.livestock_service import get_service


def _is_admin(user: Any) -> bool:
    return getattr(user, "user_type", None) == "admin" or getattr(user, "is_superuser", False) is True


class LivestockRepository:
    def __init__(self, user: Any = None):
        self._crud = get_service()
        # None = no owner scoping (admins, internal jobs)
        self._owner = None if user is None or _is_admin(user) else user

    def get_by_id(self, item_id: int) -> Optional[Dict]:
        return self._crud.find(item_id, owner=self._owner)

    def list(self, conditions: Optional[Dict] = None, skip: int = 0, limit: int = 100) -> List[Dict]:
        filters = self._crud._clean(conditions or {})
        clauses = [f't."{k}" = ?' for k in filters]
        bind: List[Any] = list(filters.values())
        scope = self._crud._scope(self._owner)
        if scope:
            clauses.append(f"({scope})")
        sql = 'SELECT t.* FROM "livestock" t'
        if clauses:
            sql += " WHERE " + " AND ".join(clauses)
        sql += " ORDER BY t.id DESC LIMIT ? OFFSET ?"
        return DB.raw(sql, bind + [int(limit), int(skip)]).result or []

    def create(self, data: Dict) -> Dict:
        return self._crud.create(data, owner=self._owner)

    def update(self, item_id: int, data: Dict) -> Optional[Dict]:
        return self._crud.update(item_id, data, owner=self._owner)

    def delete(self, item_id: int) -> bool:
        return self._crud.delete(item_id, owner=self._owner)
