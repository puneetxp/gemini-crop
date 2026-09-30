"""
Livestock listing catalog: create, search and manage animals offered for sale.

Named livestock_listing_catalog.py on purpose: `livestock_listing_service.py` is the generated CRUD
service and `php setup.php` overwrites it. Same method names as the old service so the router is unchanged.
"""

import json
import logging
from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional, Tuple

from app.core.db import DB

logger = logging.getLogger(__name__)

COLUMNS = [
    "livestock_id",
    "title",
    "description",
    "species",
    "breed",
    "age_years",
    "age_months",
    "gender",
    "quantity",
    "purpose",
    "price",
    "price_negotiable",
    "weight_kg",
    "health_status",
    "vaccination_status",
    "last_vaccination_date",
    "milk_production_liters",
    "breeding_certified",
    "breeding_certification_number",
    "genetic_lineage",
    "photos",
    "videos",
    "location_state",
    "location_district",
    "location_village",
    "latitude",
    "longitude",
    "pincode",
    "address_line",
    "farmer_contact_phone",
    "farmer_contact_email",
    "status",
]


def _value(v):
    if hasattr(v, "value"):  # enums
        return v.value
    if isinstance(v, bool):
        return 1 if v else 0
    if isinstance(v, (list, dict)):
        return json.dumps(v)
    return v


class LivestockListingService:
    def __init__(self, db=None):
        self.db = db  # unused; kept for the router's call signature

    def _format_listing_response(self, row: Dict[str, Any]) -> Dict[str, Any]:
        out = {k: float(v) if isinstance(v, Decimal) else v for k, v in row.items()}
        for k in ("photos", "videos"):
            try:
                out[k] = json.loads(out[k]) if out.get(k) else []
            except (TypeError, ValueError):
                out[k] = [out[k]]
        for k in ("price_negotiable", "breeding_certified", "featured"):
            if k in out:
                out[k] = bool(out[k])
        return out

    def _get(self, listing_id: int) -> Optional[Dict[str, Any]]:
        rows = DB.raw("SELECT * FROM livestock_listings WHERE id = ?", [listing_id]).result
        return rows[0] if rows else None

    def _owned(self, listing_id: int, user_id: int) -> Optional[Dict[str, Any]]:
        row = self._get(listing_id)
        if row and row["farmer_id"] != user_id:
            raise ValueError("Only the owner can change this listing")
        return row

    async def create_listing(self, listing, user_id: int) -> Dict[str, Any]:
        data = {
            k: _value(v) for k, v in listing.model_dump().items() if k in COLUMNS and v is not None
        }
        animal = DB.raw("SELECT * FROM livestock WHERE id = ?", [data.get("livestock_id")]).result
        if not animal or animal[0]["farmer_id"] != user_id:
            raise ValueError("Livestock not found")
        data.setdefault("species", animal[0]["species"])
        data.setdefault("breed", animal[0]["breed"])
        if "location_state" not in data or "location_district" not in data:
            data.setdefault("location_state", animal[0].get("state") or "")
            data.setdefault("location_district", animal[0].get("district") or "")
        user = DB.raw("SELECT phone, email FROM users WHERE id = ?", [user_id]).result
        if user:
            data.setdefault("farmer_contact_phone", user[0]["phone"])
            data.setdefault("farmer_contact_email", user[0]["email"])
        data["farmer_id"] = user_id
        cols = ", ".join(f'"{k}"' for k in data)
        row = DB.raw(
            f"INSERT INTO livestock_listings ({cols}) VALUES ({', '.join('?' for _ in data)}) RETURNING *",
            list(data.values()),
        ).result[0]
        return self._format_listing_response(row)

    async def get_listing(
        self, listing_id: int, increment_views: bool = False
    ) -> Optional[Dict[str, Any]]:
        if increment_views:
            rows = DB.raw(
                "UPDATE livestock_listings SET views_count = COALESCE(views_count, 0) + 1 WHERE id = ? RETURNING *",
                [listing_id],
            ).result
            return self._format_listing_response(rows[0]) if rows else None
        row = self._get(listing_id)
        return self._format_listing_response(row) if row else None

    async def update_listing(
        self, listing_id: int, listing, user_id: int
    ) -> Optional[Dict[str, Any]]:
        if not self._owned(listing_id, user_id):
            return None
        data = {
            k: _value(v)
            for k, v in listing.model_dump(exclude_unset=True).items()
            if k in COLUMNS and k != "livestock_id"
        }
        if not data:
            return await self.get_listing(listing_id)
        sets = ", ".join(f'"{k}" = ?' for k in data)
        row = DB.raw(
            f'UPDATE livestock_listings SET {sets}, "updated_at" = CURRENT_TIMESTAMP WHERE id = ? RETURNING *',
            list(data.values()) + [listing_id],
        ).result[0]
        return self._format_listing_response(row)

    async def delete_listing(self, listing_id: int, user_id: int) -> bool:
        """Soft delete: the listing becomes inactive (transactions still reference it)."""
        if not self._owned(listing_id, user_id):
            return False
        DB.raw("UPDATE livestock_listings SET status = 'inactive' WHERE id = ?", [listing_id])
        return True

    async def search_listings(self, f) -> Tuple[List[Dict[str, Any]], int]:
        where, bind = [], []
        exact = {
            "species": f.species,
            "purpose": f.purpose,
            "gender": f.gender,
            "location_state": f.location_state,
            "location_district": f.location_district,
            "health_status": f.health_status,
            "vaccination_status": f.vaccination_status,
            "status": f.status,
        }
        for column, value in exact.items():
            if value is not None:
                where.append(f'"{column}" = ?')
                bind.append(_value(value))
        if f.breed:
            where.append("breed ILIKE ?")
            bind.append(f"%{f.breed}%")
        if f.min_price is not None:
            where.append("price >= ?")
            bind.append(f.min_price)
        if f.max_price is not None:
            where.append("price <= ?")
            bind.append(f.max_price)
        age = "(COALESCE(age_years, 0) * 12 + COALESCE(age_months, 0))"
        if f.min_age_months is not None:
            where.append(f"{age} >= ?")
            bind.append(f.min_age_months)
        if f.max_age_months is not None:
            where.append(f"{age} <= ?")
            bind.append(f.max_age_months)
        if f.breeding_certified is not None:
            where.append("breeding_certified = ?")
            bind.append(1 if f.breeding_certified else 0)
        if f.featured_only:
            where.append("featured = 1")
        clause = f"WHERE {' AND '.join(where)}" if where else ""
        total = DB.raw(f"SELECT COUNT(*) AS n FROM livestock_listings {clause}", bind).result[0][
            "n"
        ]
        order = f'"{f.sort_by}" {"ASC" if f.sort_order == "asc" else "DESC"}'
        rows = DB.raw(
            f"SELECT * FROM livestock_listings {clause} ORDER BY {order} LIMIT ? OFFSET ?",
            bind + [f.limit, f.skip],
        ).result
        return [self._format_listing_response(r) for r in rows], total

    async def get_listing_analytics(
        self, listing_id: int, user_id: int
    ) -> Optional[Dict[str, Any]]:
        row = self._owned(listing_id, user_id)
        if not row:
            return None
        views, interest = row["views_count"] or 0, row["interest_count"] or 0
        age_days = max((datetime.now() - row["created_at"]).days, 1)
        return {
            "listing_id": listing_id,
            "views_count": views,
            "interest_count": interest,
            "inquiry_count": row["inquiry_count"] or 0,
            # Per-day history isn't stored, so recent windows are estimated from the lifetime average.
            "views_last_7_days": round(views * min(7, age_days) / age_days),
            "views_last_30_days": round(views * min(30, age_days) / age_days),
            "interest_last_7_days": round(interest * min(7, age_days) / age_days),
            "interest_last_30_days": round(interest * min(30, age_days) / age_days),
            "average_daily_views": round(views / age_days, 2),
            "conversion_rate": round(interest / views, 3) if views else 0.0,
        }

    async def _bump(self, listing_id: int, column: str) -> bool:
        rows = DB.raw(
            f"UPDATE livestock_listings SET {column} = COALESCE({column}, 0) + 1 WHERE id = ? AND status = 'active' RETURNING id",
            [listing_id],
        ).result
        return bool(rows)

    async def increment_interest(self, listing_id: int) -> bool:
        return await self._bump(listing_id, "interest_count")

    async def increment_inquiry(self, listing_id: int) -> bool:
        return await self._bump(listing_id, "inquiry_count")

    def generate_presigned_upload_url(
        self, filename: str, content_type: str, user_id: int
    ) -> Dict[str, Any]:
        """Media is uploaded through POST /api/v1/upload/image (stored in GCS in production)."""
        if not content_type.startswith(("image/", "video/")):
            raise ValueError("Only images and videos can be uploaded")
        return {"upload_url": "/api/v1/upload/image", "file_url": "", "expires_in": 3600}

    def recent_for(self, user_id: int, limit: int = 5) -> List[Dict[str, Any]]:
        rows = DB.raw(
            "SELECT * FROM livestock_listings WHERE farmer_id = ? ORDER BY created_at DESC LIMIT ?",
            [user_id, limit],
        ).result
        return [self._format_listing_response(r) for r in rows]
