"""
Row ownership for the /islogin/* role controllers.

"Where is what": each table's rule lives in OWNERSHIP below. A signed-in user only lists, reads,
updates and deletes rows the rule matches, and can only create rows attached to things they own.
Tables not listed are shared reference data (read-only for islogin in their model JSON crud block).
Admins use /isuper/*, which is never scoped.

Rules are SQL conditions on alias `t`; `{uid}` is the signed-in user's integer id.
"""

from typing import Dict, List, Optional

_FARMS = "SELECT id FROM farms WHERE user_id = {uid} OR owner_id = {uid}"
_PLOTS = f"SELECT id FROM farm_plots WHERE farm_id IN ({_FARMS})"
_CROPS = f"SELECT id FROM crops WHERE farm_plot_id IN ({_PLOTS})"
_LIVESTOCK = "SELECT id FROM livestock WHERE farmer_id = {uid}"
_LISTINGS = "SELECT id FROM marketplace_listings WHERE farmer_id = {uid}"
_BOOKINGS = "SELECT id FROM advance_bookings WHERE buyer_id = {uid} OR farmer_id = {uid}"
_LS_TRANSACTIONS = (
    "SELECT id FROM livestock_transactions WHERE seller_id = {uid} OR buyer_id = {uid}"
)
_PROVIDERS = "SELECT id FROM transport_providers WHERE user_id = {uid}"
_SUPPLY_REQUESTS = "SELECT id FROM supply_requests WHERE buyer_id = {uid}"

OWNERSHIP: Dict[str, str] = {
    # The user's own account row
    "users": "t.id = {uid}",
    "active_roles": "t.user_id = {uid}",
    "ai_usage_quota": "t.user_id = {uid}",
    # Farms and everything hanging off a farm
    "farms": "t.user_id = {uid} OR t.owner_id = {uid}",
    "farm_plots": f"t.farm_id IN ({_FARMS})",
    "crops": f"t.farm_plot_id IN ({_PLOTS})",
    "crop_expenses": f"t.crop_id IN ({_CROPS})",
    "crop_milestones": f"t.crop_id IN ({_CROPS})",
    "annual_strategies": f"t.farmer_id = {{uid}} OR t.farm_id IN ({_FARMS})",
    "fertilizer_applications": f"t.farm_id IN ({_FARMS})",
    "soil_test_results": f"t.farm_id IN ({_FARMS})",
    "pest_disease_alerts": f"t.farm_id IN ({_FARMS})",
    "weather_alerts": f"t.farm_id IN ({_FARMS})",
    # Livestock
    "livestock": "t.farmer_id = {uid}",
    "livestock_health_records": f"t.livestock_id IN ({_LIVESTOCK})",
    "breeding_records": "t.farmer_id = {uid}",
    "offspring": "t.farmer_id = {uid}",
    "livestock_listings": "t.farmer_id = {uid}",
    "livestock_marketplace_listings": "t.farmer_id = {uid}",
    "livestock_transactions": "t.seller_id = {uid} OR t.buyer_id = {uid}",
    # Marketplace: both sides of a deal can see it
    "marketplace_listings": "t.farmer_id = {uid}",
    "buyer_interests": f"t.listing_id IN ({_LISTINGS})",
    "advance_bookings": "t.buyer_id = {uid} OR t.farmer_id = {uid}",
    "payment_milestones": f"t.booking_id IN ({_BOOKINGS})",
    "quality_verifications": f"t.booking_id IN ({_BOOKINGS})",
    "supply_requests": "t.buyer_id = {uid}",
    "supply_matches": f"t.farmer_id = {{uid}} OR t.request_id IN ({_SUPPLY_REQUESTS})",
    # Transport
    "transport_providers": "t.user_id = {uid}",
    "transport_bookings": f"t.provider_id IN ({_PROVIDERS}) OR t.transaction_id IN ({_LS_TRANSACTIONS}) OR t.requester_id = {{uid}}",
    # Vets: the directory is readable by every signed-in user, but you only edit vets you added
    "veterinarians": "t.added_by_user_id = {uid}",
    # Added 2026-09-26 with the new soil / ROI / inbox tables
    "soil_tests": f"t.plot_id IN ({_PLOTS})",
    "soil_amendments": f"t.plot_id IN ({_PLOTS})",
    "livestock_roi_predictions": f"t.user_id = {{uid}} OR t.animal_id IN ({_LIVESTOCK})",
    "user_notifications": "t.user_id = {uid}",
    # Services: everyone signed in can browse; a service provider edits only services linked to them
    "services": "t.user_id = {uid}",
    # Voice/assistant attempts: a farmer sees only their own (admins see all via isuper)
    "voice_assist_logs": "t.user_id = {uid}",
    "crop_diagnoses": "t.user_id = {uid}",
    "satellite_observations": f"t.farm_id IN ({_FARMS})",
}

# Tables whose islogin list/read shows every row (shared directory) while writes stay owner-only.
SHARED_READ = {"veterinarians", "services"}

# On create, these columns are set to the signed-in user whatever the client sent.
OWNER_COLUMNS: Dict[str, List[str]] = {
    "active_roles": ["user_id"],
    "ai_usage_quota": ["user_id"],
    "farms": ["user_id", "owner_id"],
    "annual_strategies": ["farmer_id"],
    "livestock": ["farmer_id"],
    "breeding_records": ["farmer_id"],
    "offspring": ["farmer_id"],
    "livestock_listings": ["farmer_id"],
    "livestock_marketplace_listings": ["farmer_id"],
    "marketplace_listings": ["farmer_id"],
    "supply_requests": ["buyer_id"],
    "transport_providers": ["user_id"],
    "veterinarians": ["added_by_user_id"],
    "livestock_roi_predictions": ["user_id"],
    "services": ["user_id", "added_by_user_id"],
    "voice_assist_logs": ["user_id"],
    "crop_diagnoses": ["user_id"],
}

# On create/update, these parent ids must point at something the user owns (checked with the parent's rule).
PARENTS: Dict[str, Dict[str, str]] = {
    "farm_plots": {"farm_id": "farms"},
    "satellite_observations": {"farm_id": "farms"},
    "crops": {"farm_plot_id": "farm_plots"},
    "crop_expenses": {"crop_id": "crops"},
    "crop_milestones": {"crop_id": "crops"},
    "annual_strategies": {"farm_id": "farms"},
    "fertilizer_applications": {"farm_id": "farms", "plot_id": "farm_plots", "crop_id": "crops"},
    "soil_test_results": {"farm_id": "farms", "plot_id": "farm_plots"},
    "pest_disease_alerts": {"farm_id": "farms", "crop_id": "crops"},
    "weather_alerts": {"farm_id": "farms"},
    "livestock": {"farm_id": "farms"},
    "livestock_health_records": {"livestock_id": "livestock"},
    "breeding_records": {"livestock_id": "livestock"},
    "offspring": {"livestock_id": "livestock"},
    "soil_tests": {"plot_id": "farm_plots"},
    "soil_amendments": {"plot_id": "farm_plots", "follow_up_soil_test_id": "soil_tests"},
    "livestock_roi_predictions": {"animal_id": "livestock"},
    "livestock_listings": {"livestock_id": "livestock"},
    "livestock_marketplace_listings": {"livestock_id": "livestock"},
    "marketplace_listings": {"farm_id": "farms"},
    "payment_milestones": {"booking_id": "advance_bookings"},
    "quality_verifications": {"booking_id": "advance_bookings"},
}


def owner_condition(table: str, uid: int) -> Optional[str]:
    """SQL condition limiting `t` to rows the user owns, or None if the table isn't owner-scoped."""
    rule = OWNERSHIP.get(table)
    return f"({rule.format(uid=int(uid))})" if rule else None


def is_scoped(table: str) -> bool:
    return table in OWNERSHIP
