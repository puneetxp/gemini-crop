"""
Advance booking workflow (pre-harvest contracts between a buyer and a farmer).

Named booking_workflow.py on purpose: `advance_booking_service.py` is the generated CRUD service and
`php setup.php` overwrites it. Plain CRUD for these tables lives in the role controllers
(/islogin/advance_booking etc.); this module holds the business rules.

Status flow: pending -> confirmed -> quality_verified -> completed, or cancelled / disputed.
Payment milestones: advance (on confirm), quality_check, delivery, final.
"""

import json
import logging
from datetime import date, datetime, timedelta
from typing import Any, Dict, List, Optional

from app.core.db import DB

logger = logging.getLogger(__name__)

MILESTONE_SHARES = {"quality_check": 0.2, "delivery": 0.3}  # of the total; "final" gets the rest


def _num(v):
    return float(v) if v is not None else None


def _decode(v):
    if isinstance(v, str):
        try:
            return json.loads(v)
        except ValueError:
            return v
    return v


def _serialize(row: Dict[str, Any]) -> Dict[str, Any]:
    out = {}
    for k, v in row.items():
        if hasattr(v, "isoformat"):
            out[k] = v.isoformat()
        elif k in (
            "quantity_booked",
            "price_per_unit",
            "total_amount",
            "advance_payment_amount",
            "amount",
        ):
            out[k] = _num(v)
        elif k in ("quality_standards", "contract_terms", "quality_metrics", "photos"):
            out[k] = _decode(v)
        else:
            out[k] = v
    return out


class BookingWorkflow:
    def _get(self, booking_id: int) -> Optional[Dict[str, Any]]:
        rows = DB.raw("SELECT * FROM advance_bookings WHERE id = ?", [booking_id]).result
        return rows[0] if rows else None

    def _for_party(self, booking_id: int, user) -> Dict[str, Any]:
        booking = self._get(booking_id)
        is_admin = getattr(user, "user_type", None) == "admin"
        if not booking or (
            not is_admin and user.id not in (booking["buyer_id"], booking["farmer_id"])
        ):
            raise LookupError("Booking not found")
        return booking

    def _set_status(self, booking_id: int, status: str) -> Dict[str, Any]:
        return DB.raw(
            'UPDATE advance_bookings SET status = ?, "updated_at" = CURRENT_TIMESTAMP WHERE id = ? RETURNING *',
            [status, booking_id],
        ).result[0]

    # ── create / read ──────────────────────────────────────────────────────
    def create(
        self,
        buyer,
        listing_id: int,
        quantity: float,
        price_per_unit: float,
        advance_percent: int,
        expected_delivery_date: date,
        quality_standards: Dict,
        contract_terms: Dict,
    ) -> Dict[str, Any]:
        listing = DB.raw("SELECT * FROM marketplace_listings WHERE id = ?", [listing_id]).result
        if not listing:
            raise ValueError("Listing not found")
        listing = listing[0]
        if listing["status"] != "active":
            raise ValueError("Listing is not open for booking")
        if listing["farmer_id"] == buyer.id:
            raise ValueError("You cannot book your own listing")
        available = (
            listing["available_quantity"]
            if listing["available_quantity"] is not None
            else listing["estimated_quantity"]
        )
        if quantity > float(available):
            raise ValueError(f"Only {available} available")
        if not 20 <= advance_percent <= 50:
            raise ValueError("Advance payment must be 20-50%")

        total = round(quantity * price_per_unit, 2)
        advance = round(total * advance_percent / 100, 2)
        row = DB.raw(
            """INSERT INTO advance_bookings
               (listing_id, buyer_id, farmer_id, quantity_booked, price_per_unit, total_amount,
                advance_payment_percent, advance_payment_amount, expected_delivery_date, status,
                quality_standards, contract_terms)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'pending', ?, ?) RETURNING *""",
            [
                listing_id,
                buyer.id,
                listing["farmer_id"],
                quantity,
                price_per_unit,
                total,
                advance_percent,
                advance,
                expected_delivery_date,
                json.dumps(quality_standards or {}),
                json.dumps(contract_terms or {}, default=str),
            ],
        ).result[0]
        logger.info(f"Booking {row['id']} created for listing {listing_id} by buyer {buyer.id}")
        return _serialize(row)

    def detail(self, booking_id: int, user) -> Dict[str, Any]:
        booking = self._for_party(booking_id, user)
        listing = DB.raw(
            "SELECT * FROM marketplace_listings WHERE id = ?", [booking["listing_id"]]
        ).result
        milestones = DB.raw(
            "SELECT * FROM payment_milestones WHERE booking_id = ? ORDER BY due_date", [booking_id]
        ).result
        checks = DB.raw(
            "SELECT * FROM quality_verifications WHERE booking_id = ? ORDER BY verification_date DESC",
            [booking_id],
        ).result
        return {
            "booking": _serialize(booking),
            "listing": _serialize(listing[0]) if listing else None,
            "payment_milestones": [_serialize(m) for m in milestones],
            "quality_verifications": [
                dict(_serialize(q), passed=bool(q["passed"])) for q in checks
            ],
        }

    def list_for(
        self, user, role: Optional[str] = None, status: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        if role == "farmer":
            where, bind = "farmer_id = ?", [user.id]
        elif role == "buyer":
            where, bind = "buyer_id = ?", [user.id]
        else:
            where, bind = "(buyer_id = ? OR farmer_id = ?)", [user.id, user.id]
        if status:
            where += " AND status = ?"
            bind.append(status)
        rows = DB.raw(f"SELECT * FROM advance_bookings WHERE {where} ORDER BY id DESC", bind).result
        return [_serialize(r) for r in rows]

    # ── transitions ────────────────────────────────────────────────────────
    def confirm(self, booking_id: int, user) -> Dict[str, Any]:
        """Farmer accepts: reserve the quantity and schedule payment milestones."""
        booking = self._for_party(booking_id, user)
        if user.id != booking["farmer_id"]:
            raise PermissionError("Only the farmer can confirm a booking")
        if booking["status"] != "pending":
            raise ValueError(f"Booking is {booking['status']}")
        listing = DB.raw(
            "SELECT available_quantity, estimated_quantity FROM marketplace_listings WHERE id = ?",
            [booking["listing_id"]],
        ).result[0]
        available = (
            listing["available_quantity"]
            if listing["available_quantity"] is not None
            else listing["estimated_quantity"]
        )
        if float(booking["quantity_booked"]) > float(available):
            raise ValueError("Not enough quantity left on the listing")
        DB.raw(
            "UPDATE marketplace_listings SET available_quantity = ? WHERE id = ?",
            [int(float(available) - float(booking["quantity_booked"])), booking["listing_id"]],
        )

        total, advance = float(booking["total_amount"]), float(booking["advance_payment_amount"])
        delivery = booking["expected_delivery_date"]
        now = datetime.now()
        plan = [("advance", advance, now + timedelta(days=3))]
        for kind, share in MILESTONE_SHARES.items():
            plan.append(
                (
                    kind,
                    round(total * share, 2),
                    delivery - timedelta(days=7) if kind == "quality_check" else delivery,
                )
            )
        plan.append(
            (
                "final",
                round(total - advance - sum(a for k, a, _ in plan[1:]), 2),
                delivery + timedelta(days=7),
            )
        )
        for kind, amount, due in plan:
            DB.raw(
                "INSERT INTO payment_milestones (booking_id, milestone_type, amount, due_date) VALUES (?, ?, ?, ?)",
                [booking_id, kind, max(amount, 0), due],
            )
        return _serialize(self._set_status(booking_id, "confirmed"))

    def cancel(self, booking_id: int, user) -> Dict[str, Any]:
        booking = self._for_party(booking_id, user)
        if booking["status"] in ("completed", "cancelled"):
            raise ValueError(f"Booking is already {booking['status']}")
        if booking["status"] != "pending":  # quantity was reserved on confirm; give it back
            DB.raw(
                "UPDATE marketplace_listings SET available_quantity = COALESCE(available_quantity, 0) + ? WHERE id = ?",
                [int(float(booking["quantity_booked"])), booking["listing_id"]],
            )
        DB.raw(
            "UPDATE payment_milestones SET status = 'cancelled' WHERE booking_id = ? AND status = 'pending'",
            [booking_id],
        )
        return _serialize(self._set_status(booking_id, "cancelled"))

    def verify_quality(
        self,
        booking_id: int,
        user,
        verifier_type: str,
        grade: str,
        metrics: Dict,
        photos: List[str],
        passed: bool,
        notes: Optional[str],
    ) -> Dict[str, Any]:
        booking = self._for_party(booking_id, user)
        if booking["status"] not in ("confirmed", "quality_verified", "disputed"):
            raise ValueError("Quality can only be checked on a confirmed booking")
        DB.raw(
            """INSERT INTO quality_verifications (booking_id, verifier_type, quality_grade, quality_metrics, photos, passed, notes)
                  VALUES (?, ?, ?, ?, ?, ?, ?)""",
            [
                booking_id,
                verifier_type,
                grade,
                json.dumps(metrics or {}),
                json.dumps(photos or []),
                1 if passed else 0,
                notes,
            ],
        )
        return _serialize(
            self._set_status(booking_id, "quality_verified" if passed else "disputed")
        )

    def dispute(
        self, booking_id: int, user, reason: str, details: Optional[str], photos: List[str]
    ) -> Dict[str, Any]:
        booking = self._for_party(booking_id, user)
        if booking["status"] in ("completed", "cancelled"):
            raise ValueError(f"Booking is {booking['status']}")
        DB.raw(
            """INSERT INTO quality_verifications (booking_id, verifier_type, quality_grade, quality_metrics, photos, passed, notes)
                  VALUES (?, 'dispute', ?, ?, ?, 0, ?)""",
            [
                booking_id,
                (
                    booking.get("quality_standards")
                    and _decode(booking["quality_standards"]).get("grade")
                )
                or "NA",
                json.dumps({"raised_by": user.id, "reason": reason}),
                json.dumps(photos or []),
                details or reason,
            ],
        )
        return _serialize(self._set_status(booking_id, "disputed"))

    def complete(self, booking_id: int, user) -> Dict[str, Any]:
        booking = self._for_party(booking_id, user)
        if user.id != booking["buyer_id"] and getattr(user, "user_type", None) != "admin":
            raise PermissionError("Only the buyer can confirm delivery")
        if booking["status"] not in ("confirmed", "quality_verified"):
            raise ValueError(f"Booking is {booking['status']}")
        return _serialize(self._set_status(booking_id, "completed"))

    def record_payment(
        self,
        booking_id: int,
        user,
        milestone_type: str,
        payment_method: Optional[str],
        transaction_id: Optional[str],
    ) -> Dict[str, Any]:
        booking = self._for_party(booking_id, user)
        if user.id != booking["buyer_id"]:
            raise PermissionError("Only the buyer records payments")
        rows = DB.raw(
            """UPDATE payment_milestones SET status = 'paid', paid_date = CURRENT_TIMESTAMP,
                         payment_method = ?, transaction_id = ?, "updated_at" = CURRENT_TIMESTAMP
                         WHERE id = (SELECT id FROM payment_milestones WHERE booking_id = ? AND milestone_type = ?
                                     AND status = 'pending' ORDER BY due_date LIMIT 1) RETURNING *""",
            [payment_method, transaction_id, booking_id, milestone_type],
        ).result
        if not rows:
            raise ValueError(f"No pending {milestone_type} payment for this booking")
        return _serialize(rows[0])


booking_workflow = BookingWorkflow()
