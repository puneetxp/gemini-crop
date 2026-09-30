"""
Livestock trade workflow: a buyer's inquiry on a livestock listing through negotiation to completion.

Named livestock_trade_workflow.py on purpose: `livestock_transaction_service.py` is the generated CRUD
service and `php setup.php` overwrites it. Plain CRUD lives in /islogin/livestock_transaction.

Status flow: inquiry -> negotiation -> agreed -> completed, or cancelled from any open status.
"""

import logging
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Any, Dict, List, Optional

from app.core.db import DB

logger = logging.getLogger(__name__)

OPEN = ("inquiry", "negotiation", "agreed")
NEXT = {
    "inquiry": {"negotiation", "agreed", "cancelled"},
    "negotiation": {"agreed", "cancelled"},
    "agreed": {"completed", "cancelled"},
}


def _row(row: Dict[str, Any]) -> Dict[str, Any]:
    out = {k: float(v) if isinstance(v, Decimal) else v for k, v in row.items()}
    out["delivery_required"] = bool(out.get("delivery_required"))
    return out


def _append(existing: Optional[str], who: str, message: Optional[str]) -> Optional[str]:
    if not message:
        return existing
    line = f"[{datetime.now():%Y-%m-%d %H:%M}] {who}: {message}"
    return f"{existing}\n{line}" if existing else line


class LivestockTradeWorkflow:
    def _get(self, transaction_id: int) -> Optional[Dict[str, Any]]:
        rows = DB.raw("SELECT * FROM livestock_transactions WHERE id = ?", [transaction_id]).result
        return rows[0] if rows else None

    def _for_party(self, transaction_id: int, user) -> Dict[str, Any]:
        t = self._get(transaction_id)
        admin = getattr(user, "user_type", None) == "admin"
        if not t or (not admin and user.id not in (t["buyer_id"], t["seller_id"])):
            raise LookupError("Transaction not found")
        return t

    def _save(self, transaction_id: int, fields: Dict[str, Any]) -> Dict[str, Any]:
        sets = ", ".join(f'"{k}" = ?' for k in fields)
        row = DB.raw(
            f'UPDATE livestock_transactions SET {sets}, "updated_at" = CURRENT_TIMESTAMP WHERE id = ? RETURNING *',
            list(fields.values()) + [transaction_id],
        ).result[0]
        return _row(row)

    # ── create ─────────────────────────────────────────────────────────────
    def initiate(
        self, buyer, listing_id: int, transaction_type: str, quantity: int, **extra
    ) -> Dict[str, Any]:
        listing = DB.raw("SELECT * FROM livestock_listings WHERE id = ?", [listing_id]).result
        if not listing:
            raise LookupError("Listing not found")
        listing = listing[0]
        if listing["status"] != "active":
            raise ValueError("Listing is not active")
        if listing["farmer_id"] == buyer.id:
            raise ValueError("You cannot buy from your own listing")
        if quantity > (listing["quantity"] or 1):
            raise ValueError(f"Only {listing['quantity']} available")
        price = float(listing["price"]) * quantity
        row = DB.raw(
            """INSERT INTO livestock_transactions
               (listing_id, seller_id, buyer_id, transaction_type, quantity, agreed_price, status, buyer_message,
                buyer_contact_phone, buyer_contact_email, delivery_required, delivery_address, delivery_latitude,
                delivery_longitude)
               VALUES (?, ?, ?, ?, ?, ?, 'inquiry', ?, ?, ?, ?, ?, ?, ?) RETURNING *""",
            [
                listing_id,
                listing["farmer_id"],
                buyer.id,
                transaction_type,
                quantity,
                price,
                _append(None, "buyer", extra.get("buyer_message")),
                extra.get("buyer_contact_phone") or getattr(buyer, "phone", None),
                extra.get("buyer_contact_email") or getattr(buyer, "email", None),
                1 if extra.get("delivery_required") else 0,
                extra.get("delivery_address"),
                extra.get("delivery_latitude"),
                extra.get("delivery_longitude"),
            ],
        ).result[0]
        DB.raw(
            "UPDATE livestock_listings SET inquiry_count = COALESCE(inquiry_count, 0) + 1 WHERE id = ?",
            [listing_id],
        )
        return _row(row)

    def initiate_bulk(
        self, buyer, listing_id: int, transaction_type: str, quantities: List[int], **extra
    ) -> List[Dict]:
        listing = DB.raw(
            "SELECT quantity FROM livestock_listings WHERE id = ?", [listing_id]
        ).result
        if listing and sum(quantities) > (listing[0]["quantity"] or 1):
            raise ValueError(f"Only {listing[0]['quantity']} available")
        return [self.initiate(buyer, listing_id, transaction_type, q, **extra) for q in quantities]

    # ── read ───────────────────────────────────────────────────────────────
    def detail(self, transaction_id: int, user) -> Dict[str, Any]:
        t = _row(self._for_party(transaction_id, user))
        listing = DB.raw("SELECT * FROM livestock_listings WHERE id = ?", [t["listing_id"]]).result
        people = {
            r["id"]: r
            for r in DB.raw(
                "SELECT id, name, phone, email FROM users WHERE id IN (?, ?)",
                [t["seller_id"], t["buyer_id"]],
            ).result
        }
        t["listing"] = (
            {k: (float(v) if isinstance(v, Decimal) else v) for k, v in listing[0].items()}
            if listing
            else None
        )
        t["seller"] = people.get(t["seller_id"])
        t["buyer"] = people.get(t["buyer_id"])
        return t

    def list_for(self, user, filters: Dict[str, Any], skip: int = 0, limit: int = 20) -> List[Dict]:
        where, bind = ["(buyer_id = ? OR seller_id = ?)"], [user.id, user.id]
        for k, v in filters.items():
            where.append(f'"{k}" = ?')
            bind.append(v)
        rows = DB.raw(
            f"SELECT * FROM livestock_transactions WHERE {' AND '.join(where)} ORDER BY id DESC LIMIT ? OFFSET ?",
            bind + [limit, skip],
        ).result
        return [_row(r) for r in rows]

    def history(
        self, user_id: int, role: str, status: Optional[str], skip: int, limit: int
    ) -> List[Dict]:
        column = "buyer_id" if role == "buyer" else "seller_id"
        where, bind = f"{column} = ?", [user_id]
        if status:
            where += " AND status = ?"
            bind.append(status)
        return [
            _row(r)
            for r in DB.raw(
                f"SELECT * FROM livestock_transactions WHERE {where} ORDER BY id DESC LIMIT ? OFFSET ?",
                bind + [limit, skip],
            ).result
        ]

    def analytics(self, user_id: Optional[int], role: Optional[str]) -> Dict[str, Any]:
        where, bind = "", []
        if user_id is not None:
            if role in ("buyer", "seller"):
                where, bind = f"WHERE {role}_id = ?", [user_id]
            else:
                where, bind = "WHERE (buyer_id = ? OR seller_id = ?)", [user_id, user_id]
        rows = DB.raw(f"SELECT * FROM livestock_transactions {where}", bind).result
        total = len(rows)
        by_status: Dict[str, int] = {}
        by_type: Dict[str, int] = {}
        for r in rows:
            by_status[r["status"]] = by_status.get(r["status"], 0) + 1
            by_type[r["transaction_type"]] = by_type.get(r["transaction_type"], 0) + 1
        done = [r for r in rows if r["status"] == "completed"]
        value = sum(float(r["agreed_price"] or 0) for r in done)
        days = [
            (r["completed_at"] - r["created_at"]).total_seconds() / 86400
            for r in done
            if r.get("completed_at")
        ]
        return {
            "total_transactions": total,
            "by_status": by_status,
            "by_type": by_type,
            "total_value": round(value, 2),
            "average_transaction_value": round(value / len(done), 2) if done else 0.0,
            "completion_rate": round(len(done) / total, 3) if total else 0.0,
            "cancellation_rate": round(by_status.get("cancelled", 0) / total, 3) if total else 0.0,
            "average_time_to_completion_days": round(sum(days) / len(days), 1) if days else None,
        }

    # ── transitions ────────────────────────────────────────────────────────
    def update_status(
        self,
        transaction_id: int,
        user,
        new_status: Optional[str],
        agreed_price: Optional[float] = None,
        message: Optional[str] = None,
    ) -> Dict[str, Any]:
        t = self._for_party(transaction_id, user)
        fields: Dict[str, Any] = {}
        if new_status and new_status != t["status"]:
            if new_status not in NEXT.get(t["status"], set()):
                raise ValueError(f"Cannot move from {t['status']} to {new_status}")
            if new_status == "completed":
                return self.complete(transaction_id, user)
            if new_status == "cancelled":
                return self.cancel(transaction_id, user, message or "Cancelled")
            if new_status == "agreed" and agreed_price is None and t["agreed_price"] is None:
                raise ValueError("An agreed price is required")
            fields["status"] = new_status
        if agreed_price is not None:
            fields["agreed_price"] = agreed_price
        if message:
            role = "seller" if user.id == t["seller_id"] else "buyer"
            column = "seller_response" if role == "seller" else "buyer_message"
            fields[column] = _append(t[column], role, message)
        return self._save(transaction_id, fields) if fields else _row(t)

    def seller_reply(
        self, transaction_id: int, user, message: str, new_status: Optional[str]
    ) -> Dict[str, Any]:
        t = self._for_party(transaction_id, user)
        if user.id != t["seller_id"]:
            raise PermissionError("Only the seller can reply here")
        if t["status"] not in OPEN:
            raise ValueError(f"Transaction is {t['status']}")
        status = new_status or ("negotiation" if t["status"] == "inquiry" else t["status"])
        if status != t["status"] and status not in NEXT.get(t["status"], set()):
            raise ValueError(f"Cannot move from {t['status']} to {status}")
        return self._save(
            transaction_id,
            {"seller_response": _append(t["seller_response"], "seller", message), "status": status},
        )

    def buyer_message(self, transaction_id: int, user, message: str) -> Dict[str, Any]:
        t = self._for_party(transaction_id, user)
        if user.id != t["buyer_id"]:
            raise PermissionError("Only the buyer can send this message")
        if t["status"] not in OPEN:
            raise ValueError(f"Transaction is {t['status']}")
        return self._save(
            transaction_id, {"buyer_message": _append(t["buyer_message"], "buyer", message)}
        )

    def complete(self, transaction_id: int, user, notes: Optional[str] = None) -> Dict[str, Any]:
        """Seller confirms handover; starts the health guarantee and reduces the listing's stock."""
        t = self._for_party(transaction_id, user)
        if user.id != t["seller_id"]:
            raise PermissionError("Only the seller can complete a sale")
        if t["status"] != "agreed":
            raise ValueError("Only an agreed transaction can be completed")
        now = datetime.now()
        DB.raw(
            """UPDATE livestock_listings SET quantity = GREATEST(quantity - ?, 0),
                  status = CASE WHEN quantity - ? <= 0 THEN 'sold' ELSE status END WHERE id = ?""",
            [t["quantity"], t["quantity"], t["listing_id"]],
        )
        return self._save(
            transaction_id,
            {
                "status": "completed",
                "completed_at": now,
                "health_guarantee_expires": now + timedelta(days=t["health_guarantee_days"] or 7),
                "notes": _append(t["notes"], "seller", notes),
            },
        )

    def cancel(self, transaction_id: int, user, reason: str) -> Dict[str, Any]:
        t = self._for_party(transaction_id, user)
        if t["status"] not in OPEN:
            raise ValueError(f"Transaction is already {t['status']}")
        return self._save(
            transaction_id,
            {"status": "cancelled", "cancelled_at": datetime.now(), "cancellation_reason": reason},
        )


livestock_trade_workflow = LivestockTradeWorkflow()
