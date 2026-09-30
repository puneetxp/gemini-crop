"""
Annual Crop Strategy API endpoints
Implements AC2: Annual Crop Strategy & Recommendations (MVP Core)
"""

import json
import logging
import uuid
from datetime import datetime
from typing import Annotated, Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from app.core.auth import get_current_user
from app.core.dependencies import DB, AsyncDB, BedrockSvc, CurrentFarmer, CurrentUser
from app.orm.active_role import ActiveRole
from app.orm.annual_strategy import AnnualStrategy
from app.orm.farm import Farm
from app.schemas.crop import (
    AlternativeOption,
    AnnualStrategyResponse,
    AnnualSummary,
    MonthlyAction,
    SaveStrategyRequest,
    SaveStrategyResponse,
    SeasonalRecommendation,
    StrategyFeedbackRequest,
    StrategyListItem,
    UpdateStrategyStatusRequest,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/annual-strategy", tags=["annual-strategy"])


MONTH_ORDER: List[str] = [
    "January",
    "February",
    "March",
    "April",
    "May",
    "June",
    "July",
    "August",
    "September",
    "October",
    "November",
    "December",
]

REGIONAL_MONTHLY_ENRICHMENTS: Dict[str, Dict[str, List[str]]] = {
    "north": {
        "March": [
            "Direct-sow fast paying leafy greens like spinach/palak and amaranth to utilize the mild weather before peak heat.",
            "Start nurseries or transplant seedlings of summer vegetables (brinjal, bell pepper, chilli) under mulched beds with drip irrigation.",
            "Prepare raised beds for cucumbers and other vines, incorporating 2-3 tons FYM per acre and installing shade net/trellis support.",
            "Plan staggered sowing of cucurbit crops (cucumber, watermelon, bottle gourd) so harvests spread across late May-June.",
            "Intensify pest scouting for aphids/mites as temperatures rise; deploy sticky traps and neem-based sprays proactively.",
        ],
        "April": [
            "Transplant chilli and bell pepper saplings in the first fortnight while soil moisture is still available; maintain mulching.",
            "Sow watermelons/musk melons on sandy loam patches immediately after a light irrigation; maintain ridge-and-furrow spacing.",
            "Schedule weekly fertigation (N:K rich) for summer vegetables to sustain flowering before monsoon onset.",
        ],
        "May": [
            "Harvest early Zaid cucurbits and leafy vegetables in dawn hours to avoid heat stress and preserve quality.",
            "Install shade nets / low-cost tunnels for nursery beds to keep seedlings healthy until kharif planting.",
            "Deep plough fallow fields and incorporate crop residues + FYM so soils rest before the first monsoon rains.",
        ],
    }
}


def _detect_region(state: Optional[str]) -> Optional[str]:
    if not state:
        return None
    normalized = state.strip().lower()
    north_states = {
        "haryana",
        "punjab",
        "delhi",
        "uttar pradesh",
        "uttarakhand",
        "rajasthan",
        "himachal pradesh",
        "jammu and kashmir",
        "bihar",
        "chandigarh",
    }
    if normalized in north_states:
        return "north"
    return None


def _enrich_monthly_action_plan(
    monthly_plan: List[Dict[str, Any]], region: Optional[str], preferred_crop: Optional[str] = None
) -> List[Dict[str, Any]]:
    if not monthly_plan:
        monthly_plan = [{"month": month, "actions": []} for month in MONTH_ORDER]

    plan_index: Dict[str, Dict[str, Any]] = {}
    for entry in monthly_plan:
        month_name = entry.get("month")
        if month_name not in plan_index:
            plan_index[month_name] = entry
        entry.setdefault("actions", [])

    if region and region in REGIONAL_MONTHLY_ENRICHMENTS:
        for month, extra_actions in REGIONAL_MONTHLY_ENRICHMENTS[region].items():
            target_entry = plan_index.get(month)
            if not target_entry:
                target_entry = {"month": month, "actions": []}
                monthly_plan.append(target_entry)
                plan_index[month] = target_entry

            for action in extra_actions:
                if action not in target_entry["actions"]:
                    target_entry["actions"].append(action)

    if preferred_crop:
        march_entry = plan_index.get("March")
        if march_entry:
            custom_action = f"Finalize seed sourcing, nursery beds, and market plan for preferred crop {preferred_crop} so transplanting can start by early April."
            if custom_action not in march_entry["actions"]:
                march_entry["actions"].append(custom_action)

    # Re-order timeline to keep chronological order
    monthly_plan.sort(
        key=lambda item: (
            MONTH_ORDER.index(item["month"])
            if item.get("month") in MONTH_ORDER
            else len(MONTH_ORDER)
        )
    )

    return monthly_plan


def _filter_future_months(monthly_plan: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    if not monthly_plan:
        return monthly_plan

    current_month = datetime.now().strftime("%B")
    if current_month not in MONTH_ORDER:
        return monthly_plan

    current_index = MONTH_ORDER.index(current_month)

    # Create the rolling 12-month order starting from current_month
    ordered_months = MONTH_ORDER[current_index:] + MONTH_ORDER[:current_index]

    # Map of month name to entry in monthly_plan
    plan_by_month = {entry["month"]: entry for entry in monthly_plan if "month" in entry}

    # Build the 12-month rolling list
    rolling_plan = []
    for month in ordered_months:
        if month in plan_by_month:
            rolling_plan.append(plan_by_month[month])
        else:
            rolling_plan.append({"month": month, "actions": []})

    return rolling_plan


class AnnualStrategyRequest(BaseModel):
    """Request model for annual crop strategy generation"""

    farm_id: int = Field(..., description="Farm ID for which to generate strategy")
    year: Optional[int] = Field(None, description="Agricultural year (defaults to current year)")
    budget_per_acre: Optional[float] = Field(None, description="Budget per acre in INR")
    previous_crops: Optional[str] = Field(None, description="Previous crops grown")
    preferred_crop: Optional[str] = Field(None, description="User pre-selected crop to prioritize")
    custom_message: Optional[str] = Field(
        None, description="Additional context user wants AI to consider"
    )


async def _district_coordinates(district: str, state: Optional[str]):
    """Approximate (lat, lon) of an Indian district, or (None, None)"""
    try:
        import httpx

        from app.core.config import get_system_setting

        key = get_system_setting("OPENWEATHER_API_KEY")
        if not key or key == "test-api-key":
            return None, None
        query = ",".join(x for x in (district, state, "IN") if x)
        async with httpx.AsyncClient(timeout=10) as client:
            res = await client.get(
                "https://api.openweathermap.org/geo/1.0/direct",
                params={"q": query, "limit": 1, "appid": key},
            )
        hits = res.json() if res.status_code == 200 else []
        if hits:
            return float(hits[0]["lat"]), float(hits[0]["lon"])
    except Exception as e:
        logger.warning(f"District geocoding failed for {district}: {e}")
    return None, None


@router.post("", response_model=AnnualStrategyResponse, status_code=status.HTTP_201_CREATED)
async def generate_annual_strategy(
    request: AnnualStrategyRequest, db: AsyncDB, bedrock: BedrockSvc, current_user: CurrentUser
):
    """
    Generate comprehensive annual crop strategy using Gemini on Vertex AI
    """
    try:
        farm_result = Farm.find(request.farm_id)
        if not farm_result or not farm_result.items:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Farm with ID {request.farm_id} not found",
            )

        farm = farm_result.items

        # Verify farm ownership
        owner_id = farm.get("owner_id") or farm.get("user_id")
        if owner_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to access this farm",
            )

        # Set year to current year if not provided
        year = request.year or datetime.now().year

        logger.info(f"Generating annual strategy for farm {request.farm_id}, year {year}")

        # 1. Fetch latest daily/historical soil moisture index for farm's district
        soil_moisture = None
        try:
            from app.orm.soil_moisture_data import SoilMoistureData

            district_name = farm.get("location_district")
            if district_name:
                norm_district = district_name.strip().upper()
                moisture_records = SoilMoistureData.where(
                    {"district": norm_district, "enable": 1}
                ).get()
                if moisture_records and moisture_records.items:
                    # Get the most recent daily record
                    sorted_records = sorted(
                        moisture_records.items,
                        key=lambda r: (
                            r.get("date", "")
                            if isinstance(r.get("date"), str)
                            else str(r.get("date", ""))
                        ),
                        reverse=True,
                    )
                    soil_moisture = float(sorted_records[0].get("moisture_level", 0.0))
                    logger.info(
                        f"Retrieved live soil moisture context for strategy: {soil_moisture}%"
                    )
        except Exception as e:
            logger.error(f"Failed to fetch soil moisture context for strategy: {str(e)}")

        # 2. Fetch live weather forecast using WeatherService
        weather_forecast = None
        try:
            from app.services.weather_service import get_weather_service

            # The farm's GPS point, else the district's coordinates (farms registered by pincode)
            lat = farm.get("latitude")
            lon = farm.get("longitude")
            if (lat is None or lon is None) and farm.get("location_district"):
                lat, lon = await _district_coordinates(
                    farm.get("location_district"), farm.get("location_state")
                )
            if lat is not None and lon is not None:
                weather_svc = get_weather_service(db)
                forecast_res = await weather_svc.get_forecast(float(lat), float(lon), days=5)
                if forecast_res:
                    weather_forecast = forecast_res
                    logger.info("Retrieved live weather forecast context for strategy")
        except Exception as e:
            logger.error(f"Failed to fetch weather forecast context for strategy: {str(e)}")

        # 3. Latest Sentinel-2 crop-vigour reading for the field (needs the farm's GPS point)
        satellite_summary = None
        try:
            if farm.get("latitude") is not None and farm.get("longitude") is not None:
                import asyncio

                from app.services.satellite_health import farm_health

                health = await asyncio.wait_for(farm_health(farm), timeout=30)
                sat = (health or {}).get("summary") or {}
                if sat.get("status") == "ok":
                    satellite_summary = (
                        f"Sentinel-2 scene of {sat['observed_on']} ({sat['days_old']} days old): "
                        f"NDVI {sat.get('ndvi')} (vegetation {sat.get('vigour')}), "
                        f"NDMI {sat.get('ndmi')} (water {sat.get('water')}), trend {sat.get('trend') or 'unknown'}"
                    )
        except Exception as e:
            logger.error(f"Failed to fetch satellite context for strategy: {str(e)}")

        # 4. Soil test values stored on the farm (Soil Health Card / lab report)
        soil_nutrients = {
            k: farm.get(k)
            for k in ("nitrogen", "phosphorus", "potassium", "ph_level", "soil_ph", "organic_carbon")
            if farm.get(k) is not None
        }

        # Call Gemini
        bedrock_response = await bedrock.get_annual_crop_strategy(
            state=farm.get("location_state"),
            district=farm.get("location_district"),
            soil_type=farm.get("primary_soil_type"),
            area_acres=float(farm.get("total_area", 0)),
            irrigation_type=farm.get("irrigation_type"),
            previous_crops=request.previous_crops,
            budget_per_acre=request.budget_per_acre,
            preferred_crop=request.preferred_crop,
            custom_message=request.custom_message,
            current_date=datetime.now().date().isoformat(),
            user_id=current_user.id,
            db_session=db,
            weather_forecast=weather_forecast,
            soil_moisture=soil_moisture,
            soil_nutrients=soil_nutrients,
            satellite_summary=satellite_summary,
        )

        if not bedrock_response or "kharif" not in bedrock_response:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to generate annual strategy from Gemini",
            )

        # Extract data
        kharif = bedrock_response.get("kharif", {})
        rabi = bedrock_response.get("rabi", {})
        zaid = bedrock_response.get("zaid", {})
        annual_summary = bedrock_response.get("annual_summary", {})
        alternative_options = bedrock_response.get("alternative_options", [])
        monthly_action_plan = bedrock_response.get("monthly_action_plan", [])

        # Clean numeric fields to prevent validation errors
        def _clean_float(value: Any) -> float:
            if value is None:
                return 0.0
            if isinstance(value, (int, float)):
                return float(value)
            import re

            val_str = str(value).strip().replace(",", "")
            match = re.search(r"[-+]?\d*\.\d+|\b[-+]?\d+\b", val_str)
            if match:
                try:
                    return float(match.group(0))
                except ValueError:
                    pass
            return 0.0

        if kharif:
            if "expected_profit_per_acre" in kharif:
                kharif["expected_profit_per_acre"] = _clean_float(
                    kharif.get("expected_profit_per_acre")
                )
            if "investment_per_acre" in kharif:
                kharif["investment_per_acre"] = _clean_float(kharif.get("investment_per_acre"))
            if "confidence_score" in kharif:
                kharif["confidence_score"] = _clean_float(kharif.get("confidence_score", 0.6))

        if rabi:
            if "expected_profit_per_acre" in rabi:
                rabi["expected_profit_per_acre"] = _clean_float(
                    rabi.get("expected_profit_per_acre")
                )
            if "investment_per_acre" in rabi:
                rabi["investment_per_acre"] = _clean_float(rabi.get("investment_per_acre"))
            if "confidence_score" in rabi:
                rabi["confidence_score"] = _clean_float(rabi.get("confidence_score", 0.6))

        if zaid:
            if "expected_profit_per_acre" in zaid:
                zaid["expected_profit_per_acre"] = _clean_float(
                    zaid.get("expected_profit_per_acre")
                )
            if "investment_per_acre" in zaid:
                zaid["investment_per_acre"] = _clean_float(zaid.get("investment_per_acre"))
            if "confidence_score" in zaid:
                zaid["confidence_score"] = _clean_float(zaid.get("confidence_score", 0.6))

        if annual_summary:
            if "total_expected_profit_per_acre" in annual_summary:
                annual_summary["total_expected_profit_per_acre"] = _clean_float(
                    annual_summary.get("total_expected_profit_per_acre")
                )
            if "total_investment_per_acre" in annual_summary:
                annual_summary["total_investment_per_acre"] = _clean_float(
                    annual_summary.get("total_investment_per_acre")
                )
            if "roi_percentage" in annual_summary:
                annual_summary["roi_percentage"] = _clean_float(
                    annual_summary.get("roi_percentage")
                )
            if "sustainability_score" in annual_summary:
                annual_summary["sustainability_score"] = _clean_float(
                    annual_summary.get("sustainability_score", 0.7)
                )

        cleaned_options = []
        for opt in alternative_options:
            if isinstance(opt, dict):
                cleaned_opt = opt.copy()
                cleaned_opt["profit_difference"] = _clean_float(opt.get("profit_difference"))
                cleaned_options.append(cleaned_opt)
            else:
                cleaned_options.append(opt)
        alternative_options = cleaned_options

        region = _detect_region(farm.get("location_state"))
        monthly_action_plan = _enrich_monthly_action_plan(
            monthly_action_plan, region=region, preferred_crop=request.preferred_crop
        )
        monthly_action_plan = _filter_future_months(monthly_action_plan)

        # Get or create active role
        active_role_id = None
        farmer_role_id = 1
        active_role_query = ActiveRole.where(
            {"user_id": [current_user.id], "role_id": [farmer_role_id]}
        ).get()
        if active_role_query and active_role_query.items:
            if isinstance(active_role_query.items, list) and len(active_role_query.items) > 0:
                active_role_id = active_role_query.items[0].get("id")

        if not active_role_id:
            new_role_result = ActiveRole.create(
                {"user_id": current_user.id, "role_id": farmer_role_id, "enable": 1}
            )
            new_role_data = new_role_result.get_inserted().items
            active_role_id = new_role_data.get("id")

        # Persist strategy
        strategy_data = {
            "farm_id": request.farm_id,
            "farmer_id": owner_id,
            "year": year,
            "kharif_crop": kharif.get("recommended_crop"),
            "kharif_profit_estimate": kharif.get("expected_profit_per_acre"),
            "kharif_confidence_score": kharif.get("confidence_score", 0.0),
            "rabi_crop": rabi.get("recommended_crop"),
            "rabi_profit_estimate": rabi.get("expected_profit_per_acre"),
            "rabi_confidence_score": rabi.get("confidence_score", 0.0),
            "zaid_crop": zaid.get("recommended_crop") if zaid else None,
            "zaid_profit_estimate": zaid.get("expected_profit_per_acre", 0) if zaid else 0,
            "zaid_confidence_score": zaid.get("confidence_score", 0.0) if zaid else 0.0,
            "total_annual_profit": annual_summary.get("total_expected_profit_per_acre"),
            "implementation_timeline": json.dumps(monthly_action_plan),
            "alternative_options": json.dumps(alternative_options),
            "risk_mitigation": json.dumps(annual_summary.get("risk_mitigation", [])),
            "bedrock_response": json.dumps(bedrock_response),
            "status": "draft",
            "active_role_id": active_role_id,
        }

        strategy_result = AnnualStrategy.create(strategy_data).get_inserted()
        strategy = strategy_result.items

        # Get quota status if available
        quota_status_data = bedrock_response.pop("quota_status", None)
        quota_status = None
        if quota_status_data:
            from app.schemas.crop import QuotaStatus

            quota_status = QuotaStatus(**quota_status_data)

        return AnnualStrategyResponse(
            farm_id=request.farm_id,
            farm_name=farm.get("name", "Unknown"),
            location=f"{farm.get('location_district', '')}, {farm.get('location_state', '')}",
            kharif=kharif,
            rabi=rabi,
            zaid=zaid if zaid and zaid.get("recommended_crop") else None,
            annual_summary=annual_summary,
            alternative_options=(
                [AlternativeOption(**opt) for opt in alternative_options]
                if alternative_options
                else []
            ),
            monthly_action_plan=(
                [MonthlyAction(**action) for action in monthly_action_plan]
                if monthly_action_plan
                else []
            ),
            generated_at=datetime.now().isoformat(),
            quota_status=quota_status,
            is_fallback=bool(bedrock_response.get("is_fallback")),
        )

    except Exception as e:
        logger.error(f"Error generating annual strategy: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate annual strategy: {str(e)}",
        )


@router.post("/save", response_model=SaveStrategyResponse)
async def save_annual_strategy(request: SaveStrategyRequest, current_user: CurrentUser):
    """
    Save an annual crop strategy
    """
    try:
        user_id = current_user.id

        # Verify farm ownership
        farm_result = Farm.find(request.farm_id)
        if not farm_result or not farm_result.items:
            raise HTTPException(status_code=404, detail="Farm not found")

        farm = farm_result.items
        if (farm.get("owner_id") or farm.get("user_id")) != user_id:
            raise HTTPException(status_code=403, detail="Access denied")

        strategy_data = {
            "farm_id": request.farm_id,
            "farmer_id": user_id,
            "year": request.strategy_year,
            "kharif_crop": request.kharif_crop
            or request.strategy_data.get("kharif", {}).get("recommended_crop"),
            "rabi_crop": request.rabi_crop
            or request.strategy_data.get("rabi", {}).get("recommended_crop"),
            "zaid_crop": request.zaid_crop
            or request.strategy_data.get("zaid", {}).get("recommended_crop"),
            "total_annual_profit": request.strategy_data.get("annual_summary", {}).get(
                "total_expected_profit_per_acre", 0
            ),
            "strategy_data": request.strategy_data,
            "status": "active",
            "updated_at": datetime.now(),
        }

        existing = AnnualStrategy.where(
            {"farm_id": [request.farm_id], "year": [request.strategy_year]}
        ).first()
        if existing:
            for k, v in strategy_data.items():
                setattr(existing, k, v)
            existing.save()
            strategy = existing
        else:
            strategy_data["created_at"] = datetime.now()
            strategy = AnnualStrategy().create(strategy_data)

        return SaveStrategyResponse(
            strategy_id=str(strategy.id),
            farm_id=request.farm_id,
            strategy_year=request.strategy_year,
            message="Strategy saved successfully",
            reminders_created=0,
        )

    except Exception as e:
        logger.error(f"Error saving strategy: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to save strategy: {str(e)}")


@router.get("/list", response_model=list[StrategyListItem])
async def list_strategies(current_user: CurrentUser):
    """
    List all annual strategies for user's farms
    """
    try:
        # Get all farms for user
        farms_result = Farm.where({"user_id": [current_user.id]}).get()
        if not farms_result or not farms_result.items:
            # Try owner_id as well
            farms_result = Farm.where({"owner_id": [current_user.id]}).get()

        farm_ids = (
            [f.get("id") for f in farms_result.items]
            if farms_result and hasattr(farms_result, "items")
            else []
        )

        if not farm_ids:
            return []

        strategies_result = AnnualStrategy.where({"farm_id": farm_ids}).get()
        strategies = (
            strategies_result.items
            if strategies_result and hasattr(strategies_result, "items")
            else []
        )

        farm_names = {f.get("id"): f.get("name", "Unknown") for f in farms_result.items}

        result = []
        for s in strategies:
            result.append(
                StrategyListItem(
                    strategy_id=str(s.get("id")),
                    farm_id=s.get("farm_id"),
                    farm_name=farm_names.get(s.get("farm_id"), "Unknown"),
                    strategy_year=s.get("year"),
                    kharif_crop=s.get("kharif_crop"),
                    rabi_crop=s.get("rabi_crop"),
                    zaid_crop=s.get("zaid_crop"),
                    total_annual_profit=float(s.get("total_annual_profit") or 0),
                    is_active=s.get("status") == "active",
                    generated_at=(
                        s.get("created_at").isoformat()
                        if hasattr(s.get("created_at"), "isoformat")
                        else str(s.get("created_at"))
                    ),
                )
            )
        return result
    except Exception as e:
        logger.error(f"Error listing strategies: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{id}", response_model=AnnualStrategyResponse)
async def get_strategy(id: str, current_user: CurrentUser):
    """
    Get a specific strategy by ID
    """
    try:
        s_id = int(id)
        strategy_result = AnnualStrategy.find(s_id)
        if not strategy_result or not strategy_result.items:
            raise HTTPException(status_code=404, detail="Strategy not found")

        s = strategy_result.items
        if s.get("farmer_id") != current_user.id:
            raise HTTPException(status_code=403, detail="Access denied")

        # Parse stored data
        bedrock_response = (
            json.loads(s.get("bedrock_response")) if s.get("bedrock_response") else {}
        )
        timeline = (
            json.loads(s.get("implementation_timeline")) if s.get("implementation_timeline") else []
        )
        alternatives = (
            json.loads(s.get("alternative_options")) if s.get("alternative_options") else []
        )

        # Get farm name for response
        farm_result = Farm.find(s.get("farm_id"))
        farm_name = "Unknown"
        location = ""
        if farm_result and farm_result.items:
            farm = farm_result.items
            farm_name = farm.get("name", "Unknown")
            location = f"{farm.get('location_district', '')}, {farm.get('location_state', '')}"

        return AnnualStrategyResponse(
            farm_id=s.get("farm_id"),
            farm_name=farm_name,
            location=location,
            kharif=bedrock_response.get("kharif", {}),
            rabi=bedrock_response.get("rabi", {}),
            zaid=(
                bedrock_response.get("zaid")
                if bedrock_response.get("zaid", {}).get("recommended_crop")
                else None
            ),
            annual_summary=bedrock_response.get("annual_summary", {}),
            alternative_options=alternatives,
            monthly_action_plan=timeline,
            generated_at=(
                s.get("created_at").isoformat()
                if hasattr(s.get("created_at"), "isoformat")
                else datetime.now().isoformat()
            ),
            is_fallback=bool(bedrock_response.get("is_fallback")),
        )
    except Exception as e:
        logger.error(f"Error getting strategy: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{id}/status")
async def update_status(id: str, request: UpdateStrategyStatusRequest, current_user: CurrentUser):
    """
    Update implementation status
    """
    try:
        s_id = uuid.UUID(id)
        strategy = AnnualStrategy.find(s_id)
        if not strategy or not strategy.items:
            raise HTTPException(status_code=404, detail="Strategy not found")

        s = strategy.items
        data = s.get("strategy_data", {})
        season = request.season.lower()
        if season in data:
            data[season]["implemented"] = request.implemented
            if request.actual_results:
                data[season]["actual_results"] = request.actual_results

        strategy.strategy_data = data
        strategy.save()
        return {"status": "success", "message": "Status updated"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{id}/feedback")
async def add_feedback(id: str, request: StrategyFeedbackRequest, current_user: CurrentUser):
    """
    Add feedback
    """
    try:
        s_id = uuid.UUID(id)
        strategy = AnnualStrategy.find(s_id)
        if not strategy or not strategy.items:
            raise HTTPException(status_code=404, detail="Strategy not found")

        strategy.farmer_rating = request.rating
        strategy.farmer_feedback = request.feedback
        strategy.save()
        return {"status": "success", "message": "Feedback saved"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
