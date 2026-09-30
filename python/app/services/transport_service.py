"""
Transport coordination service for the livestock marketplace.
Handles transport provider management, booking, cost calculation, and tracking.

Uses raw SQL through app.core.db.DB (the app/orm classes are a query builder, not SQLAlchemy models).
Named transport_service.py on purpose: transport_booking_service.py / transport_provider_service.py are
generated CRUD services that `php setup.php` overwrites.

Errors: LookupError -> 404, PermissionError -> 403, ValueError -> 400 (mapped by the router).

Who can do what:
- Provider: anyone signed in can list/view; only the owning user (or an admin) can update it or see its bookings.
- Booking parties: the requester, the provider's user, and the buyer/seller of the linked livestock
  transaction. Anyone else (non-admin) gets 404 for a booking.
- Status updates (confirm / in_transit / delivered) are made by the provider's user or an admin.
- Cancel: any party while the booking is still open. Review: the requester or a transaction party
  (not the provider) once delivered, once.

Booking status flow: pending -> confirmed -> in_transit -> delivered; pending/confirmed/in_transit -> cancelled.
"""

import json
import math
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Any, Dict, List, Optional

from app.core.db import DB

AVG_SPEED_KMH = 50
DEFAULT_DISTANCE_KM = 100.0
TYPE_MULTIPLIERS = {"cattle": 1.0, "buffalo": 1.0, "goat": 0.8, "sheep": 0.8, "poultry": 0.6}
NEXT = {
    "pending": {"confirmed", "cancelled"},
    "confirmed": {"in_transit", "cancelled"},
    "in_transit": {"delivered", "cancelled"},
}
CANCELLABLE = ("pending", "confirmed", "in_transit")
PROVIDER_JSON_FIELDS = (
    "service_areas",
    "vehicle_types",
    "livestock_specialization",
    "verification_documents",
)
PROVIDER_UPDATABLE = {
    "company_name",
    "contact_person",
    "contact_phone",
    "contact_email",
    "service_areas",
    "vehicle_types",
    "livestock_specialization",
    "base_rate_per_km",
    "minimum_charge",
    "max_capacity_animals",
    "insurance_available",
    "insurance_rate_percentage",
    "license_number",
    "verification_documents",
    "status",
}


def _row(row: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    if row is None:
        return None
    return {k: float(v) if isinstance(v, Decimal) else v for k, v in row.items()}


def _val(obj: Any, key: str, default: Any = None) -> Any:
    """Read a field from a dict row or an attribute object."""
    if isinstance(obj, dict):
        v = obj.get(key, default)
    else:
        v = getattr(obj, key, default)
    return float(v) if isinstance(v, Decimal) else v


def _is_admin(user) -> bool:
    return getattr(user, "user_type", None) == "admin"


def _json_list(value: Optional[str]) -> List[str]:
    if not value:
        return []
    try:
        data = json.loads(value)
        return data if isinstance(data, list) else [str(data)]
    except (TypeError, ValueError):
        return [s.strip() for s in str(value).split(",") if s.strip()]


def _track(existing: Optional[str], status: str, message: str) -> str:
    updates = []
    if existing:
        try:
            updates = json.loads(existing)
        except (TypeError, ValueError):
            updates = []
    updates.append({"status": status, "timestamp": datetime.now().isoformat(), "message": message})
    return json.dumps(updates)


class TransportService:
    """Service for managing livestock transport coordination."""

    def __init__(self, db: Any = None):
        # `db` kept for backwards compatibility; queries go through app.core.db.DB.
        self.db = db

    # ── Providers ───────────────────────────────────────────────────────────

    def _provider(self, provider_id: int) -> Optional[Dict[str, Any]]:
        rows = DB.raw(
            "SELECT * FROM transport_providers WHERE id = ? AND enable = 1", [provider_id]
        ).result
        return _row(rows[0]) if rows else None

    def register_provider(
        self,
        user,
        company_name: str,
        contact_person: str,
        contact_phone: str,
        service_areas: List[str],
        vehicle_types: List[str],
        base_rate_per_km: float,
        minimum_charge: float,
        max_capacity_animals: int,
        contact_email: Optional[str] = None,
        livestock_specialization: Optional[List[str]] = None,
        insurance_available: bool = False,
        insurance_rate_percentage: Optional[float] = None,
        license_number: Optional[str] = None,
        verification_documents: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Register a transport provider owned by the signed-in user."""
        if insurance_available and insurance_rate_percentage is None:
            raise ValueError("insurance_rate_percentage is required when insurance is available")
        row = DB.raw(
            """INSERT INTO transport_providers
               (user_id, company_name, contact_person, contact_phone, contact_email, service_areas, vehicle_types,
                livestock_specialization, base_rate_per_km, minimum_charge, insurance_available,
                insurance_rate_percentage, max_capacity_animals, license_number, verification_documents, status)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'active') RETURNING *""",
            [
                user.id,
                company_name,
                contact_person,
                contact_phone,
                contact_email,
                json.dumps(service_areas),
                json.dumps(vehicle_types),
                json.dumps(livestock_specialization) if livestock_specialization else None,
                base_rate_per_km,
                minimum_charge,
                1 if insurance_available else 0,
                insurance_rate_percentage,
                max_capacity_animals,
                license_number,
                json.dumps(verification_documents) if verification_documents else None,
            ],
        ).result[0]
        return _row(row)

    def get_provider(self, provider_id: int) -> Dict[str, Any]:
        provider = self._provider(provider_id)
        if not provider:
            raise LookupError(f"Transport provider {provider_id} not found")
        return provider

    def search_providers(
        self,
        state: Optional[str] = None,
        district: Optional[str] = None,
        livestock_type: Optional[str] = None,
        min_capacity: Optional[int] = None,
        insurance_required: bool = False,
        verified_only: bool = False,
        user_id: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """Search active providers; service area / specialization are JSON text and filtered in Python."""
        where, bind = ["enable = 1", "status = 'active'"], []
        if verified_only:
            where.append("verified = 1")
        if insurance_required:
            where.append("insurance_available = 1")
        if min_capacity:
            where.append("max_capacity_animals >= ?")
            bind.append(min_capacity)
        if user_id is not None:
            where.append("user_id = ?")
            bind.append(user_id)
        rows = DB.raw(
            f"SELECT * FROM transport_providers WHERE {' AND '.join(where)} "
            "ORDER BY rating DESC NULLS LAST, completed_transports DESC NULLS LAST, id DESC",
            bind,
        ).result

        out = []
        for provider in (_row(r) for r in rows):
            areas = [a.lower() for a in _json_list(provider.get("service_areas"))]
            if state and not any(state.lower() in a for a in areas):
                continue
            if district and not any(district.lower() in a for a in areas):
                continue
            if livestock_type and provider.get("livestock_specialization"):
                specs = [s.lower() for s in _json_list(provider["livestock_specialization"])]
                if livestock_type.lower() not in specs:
                    continue
            out.append(provider)
        return out

    def update_provider(self, provider_id: int, user, **updates) -> Dict[str, Any]:
        """Update a provider; only its owner or an admin. Only admins may suspend."""
        provider = self.get_provider(provider_id)
        if not _is_admin(user) and provider["user_id"] != user.id:
            raise PermissionError("Only the provider's owner can update it")
        if updates.get("status") == "suspended" and not _is_admin(user):
            raise PermissionError("Only an admin can suspend a provider")

        fields: Dict[str, Any] = {}
        for key, value in updates.items():
            if key not in PROVIDER_UPDATABLE or value is None:
                continue
            if key in PROVIDER_JSON_FIELDS and isinstance(value, list):
                value = json.dumps(value)
            if key == "insurance_available":
                value = 1 if value else 0
            fields[key] = value
        if not fields:
            return provider
        sets = ", ".join(f'"{k}" = ?' for k in fields)
        row = DB.raw(
            f'UPDATE transport_providers SET {sets}, "updated_at" = CURRENT_TIMESTAMP WHERE id = ? RETURNING *',
            list(fields.values()) + [provider_id],
        ).result[0]
        return _row(row)

    # ── Cost calculation ────────────────────────────────────────────────────

    def calculate_distance(
        self,
        pickup_lat: Optional[float],
        pickup_lon: Optional[float],
        delivery_lat: Optional[float],
        delivery_lon: Optional[float],
    ) -> float:
        """Haversine distance in km; defaults to 100 km when any coordinate is missing."""
        if any(v is None for v in (pickup_lat, pickup_lon, delivery_lat, delivery_lon)):
            return DEFAULT_DISTANCE_KM
        pickup_lat, pickup_lon, delivery_lat, delivery_lon = map(
            float, (pickup_lat, pickup_lon, delivery_lat, delivery_lon)
        )
        r = 6371
        lat1, lat2 = math.radians(pickup_lat), math.radians(delivery_lat)
        d_lat = math.radians(delivery_lat - pickup_lat)
        d_lon = math.radians(delivery_lon - pickup_lon)
        a = math.sin(d_lat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(d_lon / 2) ** 2
        return round(r * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a)), 2)

    def calculate_transport_cost(
        self,
        provider: Any,
        distance_km: float,
        livestock_type: str,
        livestock_count: int,
        animal_value: float,
        insurance_opted: bool = False,
    ) -> Dict[str, float]:
        """Cost from distance, provider rates, livestock type and count. `provider` may be a row dict or object."""
        rate = float(_val(provider, "base_rate_per_km") or 0)
        minimum = float(_val(provider, "minimum_charge") or 0)
        transport_cost = max(float(distance_km) * rate, minimum)
        transport_cost *= TYPE_MULTIPLIERS.get((livestock_type or "").lower(), 1.0)
        if livestock_count > 10:
            transport_cost *= 0.90
        elif livestock_count > 5:
            transport_cost *= 0.95
        transport_cost = round(transport_cost, 2)

        insurance_cost = 0.0
        if insurance_opted and _val(provider, "insurance_available"):
            pct = float(_val(provider, "insurance_rate_percentage") or 0)
            insurance_cost = round(float(animal_value) * pct / 100, 2)

        return {
            "transport_cost": transport_cost,
            "insurance_cost": insurance_cost,
            "total_cost": round(transport_cost + insurance_cost, 2),
        }

    def estimate(
        self,
        provider_id: int,
        pickup_latitude,
        pickup_longitude,
        delivery_latitude,
        delivery_longitude,
        livestock_type: str,
        livestock_count: int,
        animal_value: float,
        insurance_opted: bool = False,
    ) -> Dict[str, Any]:
        provider = self.get_provider(provider_id)
        distance_km = self.calculate_distance(
            pickup_latitude, pickup_longitude, delivery_latitude, delivery_longitude
        )
        costs = self.calculate_transport_cost(
            provider, distance_km, livestock_type, livestock_count, animal_value, insurance_opted
        )
        return {
            "distance_km": distance_km,
            **costs,
            "provider_name": provider["company_name"],
            "estimated_travel_hours": round(distance_km / AVG_SPEED_KMH, 2),
        }

    # ── Bookings: access helpers ────────────────────────────────────────────

    def _booking(self, booking_id: int) -> Optional[Dict[str, Any]]:
        rows = DB.raw(
            """SELECT b.*, p.user_id AS provider_user_id, p.company_name AS provider_name,
                      t.buyer_id AS transaction_buyer_id, t.seller_id AS transaction_seller_id
               FROM transport_bookings b
               LEFT JOIN transport_providers p ON p.id = b.provider_id
               LEFT JOIN livestock_transactions t ON t.id = b.transaction_id
               WHERE b.id = ? AND b.enable = 1""",
            [booking_id],
        ).result
        return _row(rows[0]) if rows else None

    @staticmethod
    def _roles(booking: Dict[str, Any], user) -> set:
        roles = set()
        if booking.get("provider_user_id") == user.id:
            roles.add("provider")
        if booking.get("requester_id") == user.id:
            roles.add("requester")
        if user.id in (booking.get("transaction_buyer_id"), booking.get("transaction_seller_id")):
            roles.add("party")
        if _is_admin(user):
            roles.add("admin")
        return roles

    def _for_party(self, booking_id: int, user) -> Dict[str, Any]:
        booking = self._booking(booking_id)
        if not booking or not self._roles(booking, user):
            raise LookupError(f"Transport booking {booking_id} not found")
        return booking

    def _save(self, booking_id: int, fields: Dict[str, Any]) -> Dict[str, Any]:
        sets = ", ".join(f'"{k}" = ?' for k in fields)
        DB.raw(
            f'UPDATE transport_bookings SET {sets}, "updated_at" = CURRENT_TIMESTAMP WHERE id = ?',
            list(fields.values()) + [booking_id],
        )
        return self._booking(booking_id)

    # ── Bookings ────────────────────────────────────────────────────────────

    def create_booking(
        self,
        user,
        transaction_id: int,
        provider_id: int,
        pickup_address: str,
        delivery_address: str,
        livestock_type: str,
        livestock_count: int,
        animal_value: float,
        scheduled_pickup_date: datetime,
        pickup_latitude: Optional[float] = None,
        pickup_longitude: Optional[float] = None,
        delivery_latitude: Optional[float] = None,
        delivery_longitude: Optional[float] = None,
        insurance_opted: bool = False,
        special_instructions: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Book transport for a livestock transaction the signed-in user is buyer or seller of."""
        tx = DB.raw(
            "SELECT id, buyer_id, seller_id, status FROM livestock_transactions WHERE id = ?",
            [transaction_id],
        ).result
        if not tx or (
            not _is_admin(user) and user.id not in (tx[0]["buyer_id"], tx[0]["seller_id"])
        ):
            raise LookupError(f"Livestock transaction {transaction_id} not found")
        if tx[0]["status"] == "cancelled":
            raise ValueError("Cannot book transport for a cancelled transaction")

        provider = self.get_provider(provider_id)
        if provider.get("status") != "active":
            raise ValueError("Transport provider is not active")
        if (
            provider.get("max_capacity_animals")
            and livestock_count > provider["max_capacity_animals"]
        ):
            raise ValueError(
                f"Provider can carry at most {provider['max_capacity_animals']} animals per trip"
            )
        if insurance_opted and not provider.get("insurance_available"):
            raise ValueError("This provider does not offer insurance")

        distance_km = self.calculate_distance(
            pickup_latitude, pickup_longitude, delivery_latitude, delivery_longitude
        )
        costs = self.calculate_transport_cost(
            provider, distance_km, livestock_type, livestock_count, animal_value, insurance_opted
        )
        estimated_delivery = scheduled_pickup_date + timedelta(
            hours=distance_km / AVG_SPEED_KMH + 24
        )

        row = DB.raw(
            """INSERT INTO transport_bookings
               (transaction_id, provider_id, requester_id, pickup_address, pickup_latitude, pickup_longitude,
                delivery_address, delivery_latitude, delivery_longitude, distance_km, livestock_type,
                livestock_count, animal_value, transport_cost, insurance_opted, insurance_cost, total_cost,
                scheduled_pickup_date, estimated_delivery_date, status, tracking_updates, special_instructions)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'pending', ?, ?) RETURNING id""",
            [
                transaction_id,
                provider_id,
                user.id,
                pickup_address,
                pickup_latitude,
                pickup_longitude,
                delivery_address,
                delivery_latitude,
                delivery_longitude,
                distance_km,
                livestock_type,
                livestock_count,
                animal_value,
                costs["transport_cost"],
                1 if insurance_opted else 0,
                costs["insurance_cost"] if insurance_opted else None,
                costs["total_cost"],
                scheduled_pickup_date,
                estimated_delivery,
                _track(None, "pending", "Booking created, awaiting provider confirmation"),
                special_instructions,
            ],
        ).result[0]
        return self._booking(row["id"])

    def get_booking(self, booking_id: int, user) -> Dict[str, Any]:
        return self._for_party(booking_id, user)

    def list_bookings(
        self, user, status: Optional[str] = None, skip: int = 0, limit: int = 50
    ) -> List[Dict]:
        """Bookings the user is involved in (all bookings for an admin)."""
        where, bind = ["b.enable = 1"], []
        if not _is_admin(user):
            where.append(
                "(b.requester_id = ? OR p.user_id = ? OR t.buyer_id = ? OR t.seller_id = ?)"
            )
            bind += [user.id] * 4
        if status:
            where.append("b.status = ?")
            bind.append(status)
        rows = DB.raw(
            f"""SELECT b.*, p.user_id AS provider_user_id, p.company_name AS provider_name,
                       t.buyer_id AS transaction_buyer_id, t.seller_id AS transaction_seller_id
                FROM transport_bookings b
                LEFT JOIN transport_providers p ON p.id = b.provider_id
                LEFT JOIN livestock_transactions t ON t.id = b.transaction_id
                WHERE {' AND '.join(where)} ORDER BY b.id DESC LIMIT ? OFFSET ?""",
            bind + [limit, skip],
        ).result
        return [_row(r) for r in rows]

    def get_bookings_for_transaction(self, transaction_id: int, user) -> List[Dict[str, Any]]:
        tx = DB.raw(
            "SELECT buyer_id, seller_id FROM livestock_transactions WHERE id = ?", [transaction_id]
        ).result
        if not tx or (
            not _is_admin(user) and user.id not in (tx[0]["buyer_id"], tx[0]["seller_id"])
        ):
            raise LookupError(f"Livestock transaction {transaction_id} not found")
        rows = DB.raw(
            """SELECT b.*, p.user_id AS provider_user_id, p.company_name AS provider_name
               FROM transport_bookings b LEFT JOIN transport_providers p ON p.id = b.provider_id
               WHERE b.transaction_id = ? AND b.enable = 1 ORDER BY b.created_at DESC""",
            [transaction_id],
        ).result
        return [_row(r) for r in rows]

    def get_provider_bookings(
        self, provider_id: int, user, status: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        provider = self.get_provider(provider_id)
        if not _is_admin(user) and provider["user_id"] != user.id:
            raise PermissionError("Only the provider's owner can view its bookings")
        where, bind = "provider_id = ? AND enable = 1", [provider_id]
        if status:
            where += " AND status = ?"
            bind.append(status)
        rows = DB.raw(
            f"SELECT * FROM transport_bookings WHERE {where} ORDER BY scheduled_pickup_date DESC",
            bind,
        ).result
        return [_row(r) for r in rows]

    def update_booking_status(
        self,
        booking_id: int,
        user,
        status: str,
        message: Optional[str] = None,
        actual_pickup_date: Optional[datetime] = None,
        actual_delivery_date: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """Provider (or admin) moves a booking along pending -> confirmed -> in_transit -> delivered."""
        booking = self._for_party(booking_id, user)
        roles = self._roles(booking, user)
        if status == "cancelled":
            return self.cancel_booking(booking_id, user, message or "Cancelled")
        if not roles & {"provider", "admin"}:
            raise PermissionError("Only the transport provider can update the booking status")
        current = booking.get("status") or "pending"
        if status == current:
            raise ValueError(f"Booking is already {current}")
        if status not in NEXT.get(current, set()):
            raise ValueError(f"Cannot move booking from {current} to {status}")

        now = datetime.now()
        fields: Dict[str, Any] = {"status": status}
        if status == "in_transit":
            fields["actual_pickup_date"] = actual_pickup_date or now
        if status == "delivered":
            fields["actual_delivery_date"] = actual_delivery_date or now
            if actual_pickup_date and not booking.get("actual_pickup_date"):
                fields["actual_pickup_date"] = actual_pickup_date
        fields["tracking_updates"] = _track(
            booking.get("tracking_updates"), status, message or f"Status updated to {status}"
        )
        updated = self._save(booking_id, fields)
        if status == "delivered":
            DB.raw(
                """UPDATE transport_providers SET completed_transports = COALESCE(completed_transports, 0) + 1,
                      updated_at = CURRENT_TIMESTAMP WHERE id = ?""",
                [booking["provider_id"]],
            )
        return updated

    def add_rating_and_review(
        self, booking_id: int, user, rating: int, review: Optional[str] = None
    ) -> Dict:
        """The requester or a transaction party rates a delivered transport once."""
        booking = self._for_party(booking_id, user)
        roles = self._roles(booking, user)
        if not roles & {"requester", "party"}:
            raise PermissionError("Only the customer can review this transport")
        if booking.get("status") != "delivered":
            raise ValueError("Only a delivered transport can be reviewed")
        if booking.get("rating") is not None:
            raise ValueError("This transport has already been reviewed")

        updated = self._save(
            booking_id, {"rating": rating, "review": review, "reviewed_at": datetime.now()}
        )
        DB.raw(
            """UPDATE transport_providers
               SET rating = ROUND((COALESCE(rating, 0) * COALESCE(total_ratings, 0) + ?)
                                  / (COALESCE(total_ratings, 0) + 1), 2),
                   total_ratings = COALESCE(total_ratings, 0) + 1,
                   updated_at = CURRENT_TIMESTAMP
               WHERE id = ?""",
            [rating, booking["provider_id"]],
        )
        return updated

    def cancel_booking(self, booking_id: int, user, cancellation_reason: str) -> Dict[str, Any]:
        """Any party can cancel an open booking."""
        booking = self._for_party(booking_id, user)
        if booking.get("status") not in CANCELLABLE:
            raise ValueError(f"Booking is already {booking.get('status')}")
        return self._save(
            booking_id,
            {
                "status": "cancelled",
                "cancelled_at": datetime.now(),
                "cancellation_reason": cancellation_reason,
                "tracking_updates": _track(
                    booking.get("tracking_updates"),
                    "cancelled",
                    f"Booking cancelled: {cancellation_reason}",
                ),
            },
        )


transport_service = TransportService()
