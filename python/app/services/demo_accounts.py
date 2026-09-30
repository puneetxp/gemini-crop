"""
Temporary demo accounts

"Try the demo" gives each visitor their own farmer account with a sample farm, so visitors never see or
change each other's data. The account signs in like a normal one (Firebase ID token + refresh token, so
the session survives the 1-hour token expiry) and is refused once DEMO_TTL_HOURS have passed. An hourly
job then deletes the Firebase user and every database row that belongs to it.

Demo users are recognised by their email (cropsense-demo-<hex>@example.com, a reserved domain).
Outside production no Firebase user is created: the account gets a mock token, which only dev/test accept.
"""

import logging
import secrets
import time
from collections import defaultdict, deque
from datetime import datetime, timedelta
from typing import Any, Deque, Dict, List, Optional, Tuple

from sqlalchemy import bindparam, text
from sqlalchemy.orm import Session

from app.core.config import settings

logger = logging.getLogger(__name__)

DEMO_EMAIL_PREFIX = "cropsense-demo-"
DEMO_EMAIL_DOMAIN = "@example.com"
DEMO_EMAIL_LIKE = f"{DEMO_EMAIL_PREFIX}%{DEMO_EMAIL_DOMAIN}"

# Sample farm near Udaipur, registered the way the pincode flow does it
DEMO_FARM = {
    "name": "Demo Farm – Udaipur",
    "state": "Rajasthan",
    "district": "Udaipur",
    "village": "Balicha",
    "pincode": "313001",
    "total_area": 2.5,
    "irrigation_type": "drip",
}

PER_IP_PER_HOUR = 20  # judges on one venue Wi-Fi share an IP; DEMO_MAX_ACTIVE caps the total
_recent_by_ip: Dict[str, Deque[float]] = defaultdict(deque)


def is_demo_email(email: Optional[str]) -> bool:
    return bool(email) and email.startswith(DEMO_EMAIL_PREFIX) and email.endswith(DEMO_EMAIL_DOMAIN)


def expires_at(created_at: Any) -> Optional[datetime]:
    if isinstance(created_at, str):
        try:
            created_at = datetime.fromisoformat(created_at)
        except ValueError:
            return None
    if not isinstance(created_at, datetime):
        return None
    return created_at.replace(tzinfo=None) + timedelta(hours=settings.DEMO_TTL_HOURS)


def is_expired(email: Optional[str], created_at: Any) -> bool:
    """True for a demo account past its lifetime (accounts with an unreadable date count as expired)"""
    if not is_demo_email(email):
        return False
    end = expires_at(created_at)
    return end is None or datetime.now() >= end


def allow_ip(ip: str) -> bool:
    """At most PER_IP_PER_HOUR new demo accounts per client IP (per server instance)"""
    now = time.monotonic()
    recent = _recent_by_ip[ip]
    while recent and now - recent[0] > 3600:
        recent.popleft()
    if len(recent) >= PER_IP_PER_HOUR:
        return False
    recent.append(now)
    return True


def _production_auth() -> bool:
    return settings.ENVIRONMENT not in ("development", "test", "testing")


def create_demo_account(db: Session, lang: str = "en") -> Dict[str, Any]:
    """Create a demo farmer with a sample farm and return sign-in tokens"""
    from app.services.cognito_service import cognito_service

    purge_expired(db)
    active = db.execute(
        text("SELECT COUNT(*) FROM users WHERE email LIKE :p"), {"p": DEMO_EMAIL_LIKE}
    ).scalar() or 0
    if active >= settings.DEMO_MAX_ACTIVE:
        raise RuntimeError("Too many demo sessions are open right now. Please try again later.")

    email = f"{DEMO_EMAIL_PREFIX}{secrets.token_hex(5)}{DEMO_EMAIL_DOMAIN}"
    if _production_auth():
        password = secrets.token_urlsafe(24) + "Aa1"
        uid = cognito_service.sign_up(
            username=email, password=password, email=email, phone_number=None, full_name="Demo Farmer"
        )["user_sub"]
        tokens = cognito_service.sign_in(username=email, password=password)
    else:
        uid = f"demo-{secrets.token_hex(6)}"
        tokens = {
            "access_token": f"mock-token-{email}",
            "id_token": f"mock-token-{email}",
            "refresh_token": "mock-refresh-token",
            "expires_in": 3600,
            "token_type": "Bearer",
        }

    try:
        user_id, created_at = _create_user_and_farm(db, uid, email, lang)
    except Exception:
        db.rollback()
        if _production_auth():
            _delete_firebase_user(email)
        raise

    return {
        **tokens,
        "user": {
            "id": user_id,
            "username": email,
            "email": email,
            "name": "Demo Farmer",
            "user_type": "farmer",
            "is_demo": True,
        },
        "demo_expires_at": expires_at(created_at).astimezone().isoformat(),
    }


def _create_user_and_farm(db: Session, uid: str, email: str, lang: str) -> Tuple[int, datetime]:
    from app.services.soil_mapping import SoilMappingService

    f = DEMO_FARM
    row = db.execute(
        text(
            """INSERT INTO users (cognito_user_id, username, name, email, user_type, preferred_language,
                   pincode, state, district, village, is_active, is_verified)
               VALUES (:uid, :email, 'Demo Farmer', :email, 'farmer', :lang, :pin, :state, :district, :village, 1, 1)
               RETURNING id, created_at"""
        ),
        {"uid": uid, "email": email, "lang": lang, "pin": f["pincode"], "state": f["state"],
         "district": f["district"], "village": f["village"]},
    ).one()
    user_id, created_at = row[0], row[1]

    soil = SoilMappingService.get_likely_soil_profile(f["state"], f["district"])
    farm = {
        "user_id": user_id,
        "owner_id": user_id,
        "name": f["name"],
        "location_state": f["state"],
        "location_district": f["district"],
        "location_village": f["village"],
        "total_area": f["total_area"],
        "area_unit": "acres",
        "primary_soil_type": soil.get("primary_soil_type"),
        "irrigation_type": f["irrigation_type"],
        "is_active": True,
    }
    for k in ("nitrogen", "phosphorus", "potassium", "ph_level", "organic_carbon",
              "electrical_conductivity", "sulfur", "zinc", "iron", "boron"):
        if soil.get(k) is not None:
            farm[k] = soil[k]
    cols = ", ".join(f'"{k}"' for k in farm)
    db.execute(text(f"INSERT INTO farms ({cols}) VALUES ({', '.join(':' + k for k in farm)})"), farm)
    db.commit()
    logger.info(f"Created demo account {email} (user {user_id})")
    return user_id, created_at


# ── Clean-up ──────────────────────────────────────────────────────────────────

_FK_SQL = """
SELECT cl.relname, att.attname, par.relname
FROM pg_constraint con
JOIN pg_class cl ON cl.oid = con.conrelid
JOIN pg_class par ON par.oid = con.confrelid
JOIN pg_namespace ns ON ns.oid = cl.relnamespace
JOIN pg_attribute att ON att.attrelid = con.conrelid AND att.attnum = con.conkey[1]
WHERE con.contype = 'f' AND ns.nspname = current_schema()
"""


def _delete_tree(db: Session, fks: List[Tuple[str, str, str]], table: str, ids: List[Any], seen: set) -> None:
    """Delete rows of `table` with these ids, after every row that references them (child tables first)"""
    if not ids or table in seen:
        return
    seen = seen | {table}
    for child, column, parent in fks:
        if parent != table or child == table:
            continue
        child_ids = [
            r[0]
            for r in db.execute(
                text(f'SELECT id FROM "{child}" WHERE "{column}" IN :ids').bindparams(
                    bindparam("ids", expanding=True)
                ),
                {"ids": ids},
            )
        ]
        _delete_tree(db, fks, child, child_ids, seen)
    db.execute(
        text(f'DELETE FROM "{table}" WHERE id IN :ids').bindparams(bindparam("ids", expanding=True)),
        {"ids": ids},
    )


def _delete_firebase_user(email: str) -> None:
    from app.services.cognito_service import cognito_service

    try:
        cognito_service.admin_delete_user(email)
    except Exception as e:
        # Already gone, or Firebase unreachable: the next run retries only if the DB row is still there
        logger.warning(f"Could not delete Firebase demo user {email}: {e}")


def purge_expired(db: Session) -> int:
    """Delete expired demo accounts (Firebase user + all their rows). Returns how many were removed."""
    expired = db.execute(
        text(
            "SELECT id, email FROM users WHERE email LIKE :p"
            " AND created_at < CURRENT_TIMESTAMP - make_interval(hours => :h)"
        ),
        {"p": DEMO_EMAIL_LIKE, "h": settings.DEMO_TTL_HOURS},
    ).all()
    if not expired:
        return 0
    fks = [tuple(r) for r in db.execute(text(_FK_SQL))]
    removed = 0
    for user_id, email in expired:
        if not is_demo_email(email):
            continue
        try:
            _delete_tree(db, fks, "users", [user_id], set())
            db.commit()
            removed += 1
        except Exception as e:
            db.rollback()
            logger.error(f"Could not delete demo account {email}: {e}")
            continue
        if _production_auth():
            _delete_firebase_user(email)
    logger.info(f"Deleted {removed} expired demo account(s)")
    return removed


def start_demo_cleanup_scheduler():
    """Hourly clean-up of expired demo accounts"""
    from apscheduler.schedulers.asyncio import AsyncIOScheduler

    from app.core.database import get_db_context

    def job():
        with get_db_context() as db:
            purge_expired(db)

    scheduler = AsyncIOScheduler()
    scheduler.add_job(job, "interval", hours=1, next_run_time=datetime.now() + timedelta(minutes=1),
                      id="demo_cleanup", replace_existing=True)
    scheduler.start()
    return scheduler
