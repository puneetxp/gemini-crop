"""
Shared raw-SQL helpers for farm-owned data (farms, plots, crops, soil tests, fertilizer applications, alerts).

The app/orm classes are a query builder, not SQLAlchemy models, so custom services query through
app.core.db.DB and use these helpers for row conversion and owner checks.
Not a generated file (there is no `farm_access` table), so `php setup.php` leaves it alone.

Ownership: a farm belongs to farms.user_id. Plots, crops, soil tests and alerts are owned through
their farm. Admins (user_type == 'admin') can see everything.

Errors: LookupError -> 404 (also used for "not yours", so other users' ids are not revealed),
PermissionError -> 403, ValueError -> 400.
"""

import re
from decimal import Decimal
from typing import Any, Dict, Iterable, List, Optional

from app.core.db import DB


class Row(dict):
    """A dict row that also allows attribute access (row.col), so code written for ORM objects keeps working."""

    def __getattr__(self, key: str) -> Any:
        try:
            return self[key]
        except KeyError:
            raise AttributeError(key)

    def __setattr__(self, key: str, value: Any) -> None:
        self[key] = value


def to_row(row: Optional[Dict[str, Any]]) -> Optional[Row]:
    if row is None:
        return None
    return Row({k: float(v) if isinstance(v, Decimal) else v for k, v in row.items()})


def to_rows(rows: Iterable[Dict[str, Any]]) -> List[Row]:
    return [to_row(r) for r in rows or []]


def fetch_one(sql: str, bind: Optional[List[Any]] = None) -> Optional[Row]:
    rows = DB.raw(sql, bind or []).result
    return to_row(rows[0]) if rows else None


def fetch_all(sql: str, bind: Optional[List[Any]] = None) -> List[Row]:
    return to_rows(DB.raw(sql, bind or []).result)


def is_admin(user) -> bool:
    return getattr(user, "user_type", None) == "admin"


def _check_owner(row: Optional[Row], user, what: str, obj_id: Any) -> Row:
    if not row:
        raise LookupError(f"{what} {obj_id} not found")
    if (
        user is not None
        and not is_admin(user)
        and row.get("farm_user_id") != getattr(user, "id", None)
    ):
        raise LookupError(f"{what} {obj_id} not found")
    return row


def farm_for_user(farm_id: int, user) -> Row:
    """Farm row if `user` owns it (or is admin). `user=None` means a trusted internal call."""
    row = fetch_one("SELECT f.*, f.user_id AS farm_user_id FROM farms f WHERE f.id = ?", [farm_id])
    return _check_owner(row, user, "Farm", farm_id)


def plot_for_user(plot_id: int, user) -> Row:
    row = fetch_one(
        """SELECT p.*, f.user_id AS farm_user_id FROM farm_plots p
           JOIN farms f ON f.id = p.farm_id WHERE p.id = ?""",
        [plot_id],
    )
    return _check_owner(row, user, "Plot", plot_id)


def crop_for_user(crop_id: int, user) -> Row:
    """Crop row plus its plot's farm_id (crops link to farms through farm_plots)."""
    row = fetch_one(
        """SELECT c.*, p.farm_id AS farm_id, f.user_id AS farm_user_id FROM crops c
           LEFT JOIN farm_plots p ON p.id = c.farm_plot_id
           LEFT JOIN farms f ON f.id = p.farm_id WHERE c.id = ?""",
        [crop_id],
    )
    return _check_owner(row, user, "Crop", crop_id)


def soil_test_for_user(test_id: int, user) -> Row:
    row = fetch_one(
        """SELECT s.*, f.user_id AS farm_user_id FROM soil_test_results s
           JOIN farms f ON f.id = s.farm_id WHERE s.id = ?""",
        [test_id],
    )
    return _check_owner(row, user, "Soil test", test_id)


def owned_farm_ids(user) -> Optional[List[int]]:
    """Farm ids the user owns; None for admins (no restriction)."""
    if is_admin(user):
        return None
    return [r["id"] for r in DB.raw("SELECT id FROM farms WHERE user_id = ?", [user.id]).result]


def clean(row: Optional[Row]) -> Optional[Row]:
    """Drop the helper-only farm_user_id column before returning a row to a client."""
    if row is not None:
        row.pop("farm_user_id", None)
    return row


class NamedResult:
    """Minimal stand-in for a SQLAlchemy result (fetchone / fetchall / first / scalar / iteration).

    Rows are tuples in SELECT order that also allow attribute access by column name (row.id)."""

    def __init__(self, rows: List[Dict[str, Any]]):
        self._rows = [_TupleRow(r) for r in rows or []]

    def fetchone(self):
        return self._rows[0] if self._rows else None

    first = fetchone

    def fetchall(self):
        return list(self._rows)

    def scalar(self):
        return self._rows[0][0] if self._rows and len(self._rows[0]) else None

    def __iter__(self):
        return iter(self._rows)


class _TupleRow(tuple):
    def __new__(cls, row: Dict[str, Any]):
        obj = super().__new__(cls, tuple(row.values()))
        obj._map = dict(row)
        return obj

    def __getattr__(self, key: str) -> Any:
        try:
            return self._map[key]
        except KeyError:
            raise AttributeError(key)


_NAMED_PARAM = re.compile(r"(?<![:\w]):([A-Za-z_]\w*)")


def run_named(sql: str, params: Optional[Dict[str, Any]] = None) -> NamedResult:
    """Run SQL written with SQLAlchemy-style :name params through DB.raw (which takes ? placeholders).

    Commits immediately (DB.raw autocommits), so callers need no commit()."""
    params = params or {}
    bind: List[Any] = []

    def _sub(m):
        bind.append(params[m.group(1)])
        return "?"

    return NamedResult(DB.raw(_NAMED_PARAM.sub(_sub, sql), bind).result)
