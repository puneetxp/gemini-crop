"""
Row-Level Security and Ownership Enforcement Module for CropSense AI.
Provides table ownership registries (OWNERSHIP, SHARED_READ, OWNER_COLUMNS, PARENTS)
and verification functions to secure all /islogin and user-scoped operations.
"""
from __future__ import annotations

import logging
from typing import Any, Dict, Optional, Set, Tuple

from app.core.db import DB

logger = logging.getLogger("cropsense.ownership")

# ----------------------------------------------------------------------
# 1. SQL Ownership Rules Registry
# ----------------------------------------------------------------------
# Evaluated dynamically for authenticated users against table alias 't'
OWNERSHIP: Dict[str, str] = {
    # Users & Roles
    "users": "{alias}.id = {uid}",
    "active_roles": "{alias}.user_id = {uid}",
    "ai_usage_quota": "{alias}.user_id = {uid}",
    "user_notifications": "{alias}.user_id = {uid}",
    "push_subscriptions": "{alias}.user_id = {uid}",
    
    # Farms & Crops
    "farms": "({alias}.user_id = {uid} OR {alias}.owner_id = {uid})",
    "farm_plots": "{alias}.farm_id IN (SELECT id FROM farms WHERE user_id = {uid} OR owner_id = {uid})",
    "crops": "{alias}.farm_plot_id IN (SELECT fp.id FROM farm_plots fp JOIN farms f ON fp.farm_id = f.id WHERE f.user_id = {uid} OR f.owner_id = {uid})",
    "crop_expenses": "{alias}.crop_id IN (SELECT c.id FROM crops c JOIN farm_plots fp ON c.farm_plot_id = fp.id JOIN farms f ON fp.farm_id = f.id WHERE f.user_id = {uid} OR f.owner_id = {uid})",
    "crop_milestones": "{alias}.crop_id IN (SELECT c.id FROM crops c JOIN farm_plots fp ON c.farm_plot_id = fp.id JOIN farms f ON fp.farm_id = f.id WHERE f.user_id = {uid} OR f.owner_id = {uid})",
    "annual_strategies": "({alias}.farmer_id = {uid} OR {alias}.farm_id IN (SELECT id FROM farms WHERE user_id = {uid} OR owner_id = {uid}))",
    "crop_diagnoses": "{alias}.user_id = {uid}",
    "satellite_observations": "{alias}.farm_id IN (SELECT id FROM farms WHERE user_id = {uid} OR owner_id = {uid})",
    
    # Soil, Weather & Alerts
    "soil_tests": "{alias}.plot_id IN (SELECT fp.id FROM farm_plots fp JOIN farms f ON fp.farm_id = f.id WHERE f.user_id = {uid} OR f.owner_id = {uid})",
    "soil_test_results": "{alias}.farm_id IN (SELECT id FROM farms WHERE user_id = {uid} OR owner_id = {uid})",
    "soil_amendments": "{alias}.plot_id IN (SELECT fp.id FROM farm_plots fp JOIN farms f ON fp.farm_id = f.id WHERE f.user_id = {uid} OR f.owner_id = {uid})",
    "fertilizer_applications": "{alias}.farm_id IN (SELECT id FROM farms WHERE user_id = {uid} OR owner_id = {uid})",
    "weather_alerts": "{alias}.farm_id IN (SELECT id FROM farms WHERE user_id = {uid} OR owner_id = {uid})",
    "pest_disease_alerts": "{alias}.farm_id IN (SELECT id FROM farms WHERE user_id = {uid} OR owner_id = {uid})",
    
    # Livestock & Veterinary
    "livestock": "{alias}.farmer_id = {uid}",
    "livestock_health_records": "{alias}.livestock_id IN (SELECT id FROM livestock WHERE farmer_id = {uid})",
    "breeding_records": "{alias}.farmer_id = {uid}",
    "offspring": "{alias}.farmer_id = {uid}",
    "livestock_roi_predictions": "({alias}.user_id = {uid} OR {alias}.animal_id IN (SELECT id FROM livestock WHERE farmer_id = {uid}))",
    "livestock_listings": "{alias}.farmer_id = {uid}",
    "livestock_marketplace_listings": "{alias}.farmer_id = {uid}",
    "livestock_transactions": "({alias}.seller_id = {uid} OR {alias}.buyer_id = {uid})",
    "veterinarians": "{alias}.added_by_user_id = {uid}",
    
    # Marketplace, Logistics & Services
    "marketplace_listings": "{alias}.farmer_id = {uid}",
    "buyer_interests": "{alias}.listing_id IN (SELECT id FROM marketplace_listings WHERE farmer_id = {uid})",
    "advance_bookings": "({alias}.buyer_id = {uid} OR {alias}.farmer_id = {uid})",
    "payment_milestones": "{alias}.booking_id IN (SELECT id FROM advance_bookings WHERE buyer_id = {uid} OR farmer_id = {uid})",
    "quality_verifications": "{alias}.booking_id IN (SELECT id FROM advance_bookings WHERE buyer_id = {uid} OR farmer_id = {uid})",
    "supply_requests": "{alias}.buyer_id = {uid}",
    "supply_matches": "({alias}.farmer_id = {uid} OR {alias}.request_id IN (SELECT id FROM supply_requests WHERE buyer_id = {uid}))",
    "transport_providers": "{alias}.user_id = {uid}",
    "transport_bookings": "({alias}.provider_id IN (SELECT id FROM transport_providers WHERE user_id = {uid}) OR {alias}.transaction_id IN (SELECT id FROM livestock_transactions WHERE seller_id = {uid} OR buyer_id = {uid}) OR {alias}.requester_id = {uid})",
    "services": "{alias}.user_id = {uid}",
    "voice_assist_logs": "{alias}.user_id = {uid}",
}

# ----------------------------------------------------------------------
# 2. Shared Read Registry
# ----------------------------------------------------------------------
# Directories where all authenticated users have read access, but writes are restricted to owners
SHARED_READ: Set[str] = {
    "veterinarians",
    "services",
    "marketplace_listings",
    "livestock_listings",
    "transport_providers",
}

# ----------------------------------------------------------------------
# 3. Owner Columns Enforcer
# ----------------------------------------------------------------------
# Auto-populated with verified caller user ID on POST (creation)
OWNER_COLUMNS: Dict[str, str] = {
    "farms": "user_id",
    "livestock": "farmer_id",
    "supply_requests": "buyer_id",
    "transport_bookings": "requester_id",
    "marketplace_listings": "farmer_id",
    "livestock_listings": "farmer_id",
    "livestock_marketplace_listings": "farmer_id",
    "breeding_records": "farmer_id",
    "offspring": "farmer_id",
    "veterinarians": "added_by_user_id",
    "services": "user_id",
    "crop_diagnoses": "user_id",
    "voice_assist_logs": "user_id",
    "user_notifications": "user_id",
    "push_subscriptions": "user_id",
    "ai_usage_quota": "user_id",
    "transport_providers": "user_id",
}

# ----------------------------------------------------------------------
# 4. Parent Foreign Key Ownership Verification
# ----------------------------------------------------------------------
# (foreign_key_column, parent_table, parent_owner_rule_template)
PARENTS: Dict[str, Tuple[str, str, str]] = {
    "farm_plots": (
        "farm_id",
        "farms",
        "id = {fk_val} AND (user_id = {uid} OR owner_id = {uid})",
    ),
    "crops": (
        "farm_plot_id",
        "farm_plots",
        "id = {fk_val} AND farm_id IN (SELECT id FROM farms WHERE user_id = {uid} OR owner_id = {uid})",
    ),
    "crop_expenses": (
        "crop_id",
        "crops",
        "id = {fk_val} AND farm_plot_id IN (SELECT fp.id FROM farm_plots fp JOIN farms f ON fp.farm_id = f.id WHERE f.user_id = {uid} OR f.owner_id = {uid})",
    ),
    "crop_milestones": (
        "crop_id",
        "crops",
        "id = {fk_val} AND farm_plot_id IN (SELECT fp.id FROM farm_plots fp JOIN farms f ON fp.farm_id = f.id WHERE f.user_id = {uid} OR f.owner_id = {uid})",
    ),
    "livestock_health_records": (
        "livestock_id",
        "livestock",
        "id = {fk_val} AND farmer_id = {uid}",
    ),
    "payment_milestones": (
        "booking_id",
        "advance_bookings",
        "id = {fk_val} AND (buyer_id = {uid} OR farmer_id = {uid})",
    ),
    "quality_verifications": (
        "booking_id",
        "advance_bookings",
        "id = {fk_val} AND (buyer_id = {uid} OR farmer_id = {uid})",
    ),
}


# ----------------------------------------------------------------------
# Security Verification Helpers
# ----------------------------------------------------------------------
def get_ownership_clause(table: str, user_id: int | str, alias: str = "t") -> Optional[str]:
    """Return the SQL WHERE snippet scoping access to rows owned by user_id."""
    template = OWNERSHIP.get(table)
    if not template:
        return None
    try:
        uid_int = int(user_id)
    except (ValueError, TypeError):
        uid_int = 0
    return template.format(alias=alias, uid=uid_int)


def is_shared_read(table: str) -> bool:
    """Return True if the table allows directory-style shared reading across authenticated users."""
    return table in SHARED_READ


def enforce_owner_columns(table: str, payload: Dict[str, Any], user_id: int | str) -> Dict[str, Any]:
    """Force caller user ID into designated owner column, stripping spoofed client values."""
    col = OWNER_COLUMNS.get(table)
    if col:
        try:
            uid_val = int(user_id)
        except (ValueError, TypeError):
            uid_val = user_id
        payload[col] = uid_val
    return payload


def validate_parent_ownership(table: str, payload: Dict[str, Any], user_id: int | str) -> bool:
    """Validate that the foreign key record referenced in payload belongs to caller."""
    parent_rule = PARENTS.get(table)
    if not parent_rule:
        return True

    fk_col, parent_table, condition_tmpl = parent_rule
    fk_val = payload.get(fk_col)
    if fk_val is None:
        # Field not provided in payload; cannot validate or not required
        return True

    try:
        uid_int = int(user_id)
        fk_int = int(fk_val)
    except (ValueError, TypeError):
        return False

    condition = condition_tmpl.format(fk_val=fk_int, uid=uid_int)
    sql = f"SELECT 1 FROM {parent_table} WHERE {condition} LIMIT 1"
    res = DB.raw(sql).exe().first()
    return bool(res)


def can_access(table: str, record_id: Any, user: Dict[str, Any], action: str = "read") -> bool:
    """Check if the given user has permission to perform action on specific record."""
    if not user:
        return False

    # Admin role bypasses all ownership restrictions
    roles = user.get("roles", [])
    if "admin" in roles or user.get("role") == "admin":
        return True

    user_id = user.get("id")
    if not user_id:
        return False

    if action == "read" and is_shared_read(table):
        return True

    clause = get_ownership_clause(table, user_id, alias="t")
    if not clause:
        # Reference tables without ownership rules are read-only for users
        return action == "read"

    sql = f"SELECT 1 FROM {table} t WHERE t.id = %(rid)s AND {clause} LIMIT 1"
    row = DB.raw(sql, {"rid": record_id}).exe().first()
    return bool(row)


def owner_condition(table: str, uid: int) -> Optional[str]:
    """SQL condition limiting 't' to rows the user owns, or None if un-scoped."""
    clause = get_ownership_clause(table, uid, alias="t")
    return f"({clause})" if clause else None


def is_scoped(table: str) -> bool:
    """Check if table has row-level ownership rules."""
    return table in OWNERSHIP

