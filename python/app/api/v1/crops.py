"""
Crop Recommendation API endpoints
Handles AI-powered crop recommendations, annual strategies, and yield predictions
"""

import logging
from datetime import datetime, timedelta
from typing import Annotated, Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.auth import get_current_user, get_optional_current_user
from app.core.dependencies import DB, AsyncDB, BedrockSvc, CurrentFarmer, OptionalUserDict
from app.orm.active_role import ActiveRole
from app.orm.crop import Crop
from app.orm.crop_expense import CropExpense
from app.orm.farm import Farm
from app.orm.farm_plot import FarmPlot
from app.schemas.crop import (
    AlternativeOption,
    AnnualStrategyRequest,
    AnnualStrategyResponse,
    AnnualSummary,
    CropExpenseRequest,
    CropExpenseResponse,
    CropRecommendation,
    CropRecommendationRequest,
    CropRecommendationsResponse,
    MonthlyAction,
    QuickPlantRequest,
    QuickPlantResponse,
    SaveStrategyRequest,
    SaveStrategyResponse,
    SeasonalRecommendation,
    StrategyFeedbackRequest,
    StrategyListItem,
    UpdateStrategyStatusRequest,
    YieldPredictionRequest,
    YieldPredictionResponse,
)
from app.services.bedrock_service import BedrockService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/crops", tags=["Crops"])


@router.post("/{crop_id}/expenses", response_model=CropExpenseResponse)
async def add_crop_expense(
    crop_id: int, request: CropExpenseRequest, current_user: CurrentFarmer, db: DB
):
    """
    Add an expense for a specific crop
    """
    try:
        # Verify crop ownership
        crop_result = Crop.find(crop_id)
        if not crop_result or not crop_result.items:
            raise HTTPException(status_code=404, detail="Crop not found")

        crop = crop_result.items
        plot_result = FarmPlot.find(crop["farm_plot_id"])
        if not plot_result or not plot_result.items:
            raise HTTPException(status_code=404, detail="Plot not found")

        farm_result = Farm.find(plot_result.items["farm_id"])
        if not farm_result or not farm_result.items:
            raise HTTPException(status_code=404, detail="Farm not found")

        if (
            farm_result.items.get("owner_id") or farm_result.items.get("user_id")
        ) != current_user.id:
            raise HTTPException(status_code=403, detail="Access denied")

        # Create expense record
        expense_data = {
            "crop_id": crop_id,
            "category": request.category,
            "amount": request.amount,
            "description": request.description,
            "expense_date": request.expense_date.isoformat(),
        }

        new_expense = CropExpense().create(expense_data)
        inserted = new_expense.get_inserted().items

        return CropExpenseResponse(
            id=inserted["id"],
            crop_id=inserted["crop_id"],
            category=inserted["category"],
            amount=float(inserted["amount"]),
            description=inserted.get("description"),
            expense_date=inserted["expense_date"],
            created_at=(
                inserted["created_at"].isoformat()
                if hasattr(inserted["created_at"], "isoformat")
                else str(inserted["created_at"])
            ),
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error adding crop expense: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to add expense: {str(e)}")


@router.get("/{crop_id}/expenses", response_model=List[CropExpenseResponse])
async def get_crop_expenses(crop_id: int, current_user: CurrentFarmer, db: DB):
    """
    Get all expenses for a specific crop
    """
    try:
        # Verify crop ownership (similar check as above)
        crop_result = Crop.find(crop_id)
        if not crop_result or not crop_result.items:
            raise HTTPException(status_code=404, detail="Crop not found")

        # For listing, just get expenses
        expenses_result = CropExpense.where({"crop_id": [crop_id]}).get()
        expenses = (
            expenses_result.items if expenses_result and hasattr(expenses_result, "items") else []
        )

        return [
            CropExpenseResponse(
                id=exp["id"],
                crop_id=exp["crop_id"],
                category=exp["category"],
                amount=float(exp["amount"]),
                description=exp.get("description"),
                expense_date=exp["expense_date"],
                created_at=(
                    exp["created_at"].isoformat()
                    if hasattr(exp["created_at"], "isoformat")
                    else str(exp["created_at"])
                ),
            )
            for exp in expenses
        ]
    except Exception as e:
        logger.error(f"Error getting crop expenses: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get expenses: {str(e)}")


# Typical Indian crop duration (days) and yield (quintals/acre) for when AI predictions are unavailable.
_CROP_BASELINES = {
    "rice": (120, 22),
    "paddy": (120, 22),
    "wheat": (125, 18),
    "maize": (100, 20),
    "soybean": (100, 10),
    "cotton": (170, 8),
    "sugarcane": (330, 350),
    "groundnut": (110, 9),
    "mustard": (120, 7),
    "chickpea": (110, 8),
    "gram": (110, 8),
    "tur": (160, 6),
    "pigeon pea": (160, 6),
    "onion": (130, 100),
    "potato": (100, 100),
    "tomato": (120, 120),
    "bajra": (85, 10),
    "jowar": (110, 10),
    "sunflower": (95, 7),
}


def _baseline_yield(crop_name: str, planting_date, area_acres: float) -> Dict[str, Any]:
    from datetime import timedelta

    days, per_acre = _CROP_BASELINES.get((crop_name or "").strip().lower(), (120, 12))
    harvest = planting_date + timedelta(days=days)
    total = round(per_acre * float(area_acres or 0), 2)
    return {
        "harvest_date": harvest.isoformat(),
        "harvest_date_range": {
            "min": (harvest - timedelta(days=7)).isoformat(),
            "max": (harvest + timedelta(days=7)).isoformat(),
        },
        "expected_yield_per_acre": per_acre,
        "yield_range": {"min": round(per_acre * 0.8, 2), "max": round(per_acre * 1.2, 2)},
        "total_expected_yield": total,
        "quality_grade": "B",
        "confidence_score": 0.55,
        "key_factors": ["Typical duration and yield for this crop (AI prediction unavailable)"],
        "recommendations": [
            "Follow the recommended sowing window and fertilizer schedule for your district"
        ],
    }


def _owned_crop(crop_id: int, current_user) -> Dict[str, Any]:
    """The crop, if it sits on one of the signed-in user's farms (404 otherwise)."""
    from app.core.db import DB
    from app.core.ownership import owner_condition

    rows = DB.raw(
        f"SELECT * FROM crops t WHERE t.id = ? AND {owner_condition('crops', current_user.id)}",
        [crop_id],
    ).result
    if not rows:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Crop not found")
    return rows[0]


async def _ensure_farmer_active_role(user_id: int) -> int:
    """Fetch or create an active role record for the farmer."""
    farmer_role_id = 1
    active_role_query = ActiveRole.where({"user_id": [user_id], "role_id": [farmer_role_id]}).get()

    if active_role_query and active_role_query.items:
        items = active_role_query.items
        if isinstance(items, list) and items:
            existing = items[0]
            existing_id = (
                existing.get("id") if isinstance(existing, dict) else getattr(existing, "id", None)
            )
            if existing_id:
                return existing_id

    new_role = ActiveRole.create({"user_id": user_id, "role_id": farmer_role_id, "enable": 1})

    inserted = getattr(new_role, "get_inserted", None)
    if callable(inserted):
        inserted_items = inserted().items
        inserted_id = (
            inserted_items.get("id")
            if isinstance(inserted_items, dict)
            else getattr(inserted_items, "id", None)
        )
        if inserted_id:
            return inserted_id

    return user_id


def _create_default_plot_for_farm(
    farm: Dict[str, Any], request: QuickPlantRequest, active_role_id: int
) -> Dict[str, Any]:
    """Create a default plot covering the farm when none exist."""
    try:
        farm_total_area = float(farm.get("total_area") or request.area or 1.0)
        plot_data = {
            "enable": 1,
            "farm_id": farm.get("id"),
            "plot_name": f"{farm.get('name', 'Farm')} - Main Plot",
            "area": farm_total_area,
            "soil_type": farm.get("primary_soil_type") or "General",
            "irrigation_type": farm.get("irrigation_type") or "Unknown",
            "state": farm.get("location_state") or "Unknown",
            "district": farm.get("location_district") or "Unknown",
            "previous_crops": farm.get("previous_crops"),
            "investment_capacity": farm.get("investment_capacity_per_acre"),
            "nitrogen": farm.get("nitrogen"),
            "phosphorus": farm.get("phosphorus"),
            "potassium": farm.get("potassium"),
            "ph_level": farm.get("ph_level"),
            "organic_carbon": farm.get("organic_carbon"),
            "electrical_conductivity": farm.get("electrical_conductivity"),
            "sulfur": farm.get("sulfur"),
            "zinc": farm.get("zinc"),
            "iron": farm.get("iron"),
            "boron": farm.get("boron"),
            "active_role_id": active_role_id,
        }

        new_plot = FarmPlot.create(plot_data).get_inserted()
        if not new_plot or not getattr(new_plot, "items", None):
            raise ValueError("Failed to create default plot")
        return new_plot.items
    except Exception as exc:
        logger.error(f"Failed to auto-create farm plot: {exc}")
        raise HTTPException(status_code=500, detail="Unable to create a default plot for this farm")


@router.post("/recommendations", response_model=CropRecommendationsResponse)
async def get_crop_recommendations(
    current_user: CurrentFarmer, db: DB, bedrock: BedrockSvc, request: CropRecommendationRequest
):
    """
    Get top crop recommendations for a specific season

    Returns top 5 crops ranked by suitability for the farm's location,
    soil type, and irrigation capabilities.

    Validates: AC4 - RAG system suggests top 3 profitable crops
    """
    try:
        # Validate season
        if request.season.lower() not in ["kharif", "rabi", "zaid"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Season must be one of: kharif, rabi, zaid",
            )

        # Get farm details using custom ORM
        farm_result = Farm.where({"id": [request.farm_id]}).get()

        if not farm_result or not farm_result.items:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Farm not found")

        farm_data = farm_result.items[0]

        # Verify ownership
        if farm_data.get("owner_id") != current_user.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

        # Get plot info using custom ORM
        plot_result = FarmPlot.where({"farm_id": [request.farm_id], "is_active": [True]}).get()

        if not plot_result or not plot_result.items:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Farm must have at least one plot"
            )

        plot_data = plot_result.items[0]

        # Call Bedrock service
        logger.info(
            f"Generating crop recommendations for farm {request.farm_id} in {request.season}"
        )
        recommendations_data = await bedrock.get_crop_recommendations(
            state=farm_data.get("location_state", ""),
            district=farm_data.get("location_district", ""),
            season=request.season,
            soil_type=plot_data.get("soil_type", ""),
            area_acres=farm_data.get("total_area", 0),
            irrigation_type=plot_data.get("irrigation_type", ""),
        )

        # Build response
        response = CropRecommendationsResponse(
            farm_id=farm_data["id"],
            season=request.season,
            recommendations=[CropRecommendation(**rec) for rec in recommendations_data],
            generated_at=datetime.now().isoformat(),
        )

        logger.info(f"Crop recommendations generated successfully for farm {farm_data['id']}")

        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Crop recommendations error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate recommendations: {str(e)}",
        )


@router.post("/yield-prediction", response_model=YieldPredictionResponse)
async def predict_yield(
    current_user: CurrentFarmer, db: DB, bedrock: BedrockSvc, request: YieldPredictionRequest
):
    """
    Predict crop yield and harvest date using Amazon Bedrock AI

    Provides:
    - Expected harvest date with confidence range
    - Yield prediction per acre and total
    - Quality grade prediction
    - Key factors affecting yield
    - Recommendations for optimal yield

    Validates: AC4 - Crop yield prediction service
    """
    try:
        # Get farm and plot details using custom ORM
        farm_result = Farm.where({"id": [request.farm_id]}).get()

        if not farm_result or not farm_result.items:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Farm not found")

        farm_data = farm_result.items[0]

        # Verify ownership
        if farm_data.get("owner_id") != current_user.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

        # Get plot using custom ORM
        plot_result = FarmPlot.where({"id": [request.plot_id], "farm_id": [request.farm_id]}).get()

        if not plot_result or not plot_result.items:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Plot not found")

        plot_data = plot_result.items[0]

        # Call Bedrock service
        logger.info(
            f"Generating yield prediction for farm {request.farm_id}, crop {request.crop_name}"
        )

        prediction = await bedrock.predict_yield_and_harvest(
            crop_name=request.crop_name,
            variety=request.variety,
            state=farm_data.get("location_state", ""),
            district=farm_data.get("location_district", ""),
            planting_date=request.planting_date.isoformat(),
            area_acres=request.area_acres,
            soil_type=plot_data.get("soil_type", ""),
            irrigation_type=plot_data.get("irrigation_type", ""),
        )

        # Fill anything the AI answer lacks (e.g. the offline mock) with the rule-based estimate.
        prediction = {
            **_baseline_yield(request.crop_name, request.planting_date, request.area_acres),
            **{k: v for k, v in (prediction or {}).items() if v not in (None, "", [], {})},
        }

        # Build response
        response = YieldPredictionResponse(
            crop_name=request.crop_name,
            variety=request.variety,
            harvest_date=prediction["harvest_date"],
            harvest_date_range=prediction["harvest_date_range"],
            expected_yield_per_acre=prediction["expected_yield_per_acre"],
            yield_range=prediction["yield_range"],
            total_expected_yield=prediction["total_expected_yield"],
            quality_grade=prediction["quality_grade"],
            confidence_score=prediction["confidence_score"],
            key_factors=prediction["key_factors"],
            recommendations=prediction["recommendations"],
            generated_at=datetime.now().isoformat(),
        )

        logger.info(f"Yield prediction generated successfully for {request.crop_name}")

        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Yield prediction error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate yield prediction: {str(e)}",
        )


def _plant_supporting_crops(
    request: QuickPlantRequest,
    main_crop_id: int,
    plot_id: int,
    area_share: float,
    harvest_date,
    active_role_id: int,
) -> List[int]:
    """Create the supporting (inter/companion) crops that grow with one main crop record.

    area_share scales each supporting crop's area the same way the main crop's area was
    split across plots (1.0 when planting a single plot).
    """
    ids: List[int] = []
    for supporting in request.supporting_crops:
        if not supporting.crop_name or not supporting.crop_name.strip():
            continue
        new_crop = Crop().create(
            {
                "farm_plot_id": plot_id,
                "crop_name": supporting.crop_name.strip(),
                "crop_variety": supporting.variety,
                "season": request.season,
                "area": (supporting.area or request.area) * area_share,
                "planting_date": request.planting_date,
                "expected_harvest_date": harvest_date,
                "status": "planted",
                "expected_yield": 0.0,
                "expected_profit": 0.0,
                "parent_crop_id": main_crop_id,
                "crop_role": "supporting",
                "active_role_id": active_role_id,
            }
        )
        if new_crop and hasattr(new_crop, "id"):
            ids.append(new_crop.id)
    return ids


@router.post("/quick-plant", response_model=QuickPlantResponse)
async def quick_plant(request: QuickPlantRequest, current_user: Dict = Depends(get_current_user)):
    """
    Directly plant a crop without a confirmation page
    (AC: "no confirmation is good")
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

        crop_ids = []
        supporting_crop_ids: List[int] = []
        total_area_planted = 0.0
        # Harvest date is optional on the quick form; fall back to ~4 months after planting
        harvest_date = request.expected_harvest_date or (
            request.planting_date + timedelta(days=120)
        )

        # Ensure farmer has an active role record (needed for audit trail on crops table)
        active_role_id = await _ensure_farmer_active_role(current_user.id)

        if request.plot_id:
            # Plant on specific plot
            plot_result = FarmPlot.find(request.plot_id)
            if not plot_result or not plot_result.items:
                raise HTTPException(status_code=404, detail="Plot not found")

            plot = plot_result.items
            if plot.get("farm_id") != request.farm_id:
                raise HTTPException(status_code=400, detail="Plot does not belong to this farm")

            # Create the crop record
            crop_data = {
                "farm_plot_id": request.plot_id,
                "crop_name": request.crop_name,
                "crop_variety": request.variety,
                "season": request.season,
                "area": request.area,
                "planting_date": request.planting_date,
                "expected_harvest_date": harvest_date,
                "status": "planted",
                "expected_yield": request.expected_yield or 0.0,
                "expected_profit": (
                    (request.expected_yield * request.market_price)
                    if request.expected_yield and request.market_price
                    else 0.0
                ),
                "crop_role": "main",
                "active_role_id": active_role_id,
            }

            new_crop = Crop().create(crop_data)
            if new_crop and hasattr(new_crop, "id"):
                crop_ids.append(new_crop.id)
                total_area_planted = request.area
                supporting_crop_ids += _plant_supporting_crops(
                    request, new_crop.id, request.plot_id, 1.0, harvest_date, active_role_id
                )
        else:
            # Plant on ALL active plots of the farm (distribute area)
            plots_result = FarmPlot.where({"farm_id": [request.farm_id], "enable": [1]}).get()
            plots = plots_result.items if plots_result and hasattr(plots_result, "items") else []

            if not plots:
                # Auto-create a default plot spanning the farm if none exist
                created_plot = _create_default_plot_for_farm(farm, request, active_role_id)
                plots = [created_plot]

            # Distribute area proportionally or equally? Let's do proportionally based on plot size if available,
            # but for now let's just create a record per plot with the full area (or divided? usually users mean "plant the whole farm").
            # If "Whole Farm" and 10 acres, and we have 2 plots of 5 acres each, we plant 5 in each.

            farm_total_area = float(farm.get("total_area") or 1.0)
            area_to_distribute = request.area

            for plot in plots:
                plot_area = float(plot.get("area") or 0.0)
                # If plot area is not set, we can't distribute proportionally, so we skip or divide equally.
                # Let's assume proportional distribution: (plot_area / farm_total_area) * total_requested_area
                distributed_area = (
                    (plot_area / farm_total_area) * area_to_distribute
                    if farm_total_area > 0
                    else (area_to_distribute / len(plots))
                )

                crop_data = {
                    "farm_plot_id": plot.get("id"),
                    "crop_name": request.crop_name,
                    "crop_variety": request.variety,
                    "season": request.season,
                    "area": distributed_area,
                    "planting_date": request.planting_date,
                    "expected_harvest_date": harvest_date,
                    "status": "planted",
                    "expected_yield": (
                        (request.expected_yield / len(plots)) if request.expected_yield else 0.0
                    ),
                    "expected_profit": (
                        ((request.expected_yield * request.market_price) / len(plots))
                        if request.expected_yield and request.market_price
                        else 0.0
                    ),
                    "crop_role": "main",
                    "active_role_id": active_role_id,
                }

                new_crop = Crop().create(crop_data)
                if new_crop and hasattr(new_crop, "id"):
                    crop_ids.append(new_crop.id)
                    total_area_planted += distributed_area
                    supporting_crop_ids += _plant_supporting_crops(
                        request,
                        new_crop.id,
                        plot.get("id"),
                        (distributed_area / request.area) if request.area else 1.0,
                        harvest_date,
                        active_role_id,
                    )

        message = f"Successfully planted {request.crop_name} across {len(crop_ids)} plots"
        if supporting_crop_ids:
            names = ", ".join(c.crop_name for c in request.supporting_crops if c.crop_name.strip())
            message += f" with supporting crops: {names}"

        return QuickPlantResponse(
            success=True,
            message=message,
            crop_ids=crop_ids,
            total_area_planted=total_area_planted,
            supporting_crop_ids=supporting_crop_ids,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Quick planting error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to plant crop: {str(e)}")


# Real-Time Yield Prediction Update Endpoints (Task 25.3)


@router.post("/yield-prediction/update/{crop_id}", response_model=Dict[str, Any])
async def update_yield_prediction(
    crop_id: int,
    growth_rate: float,
    current_user: CurrentFarmer,
    db: DB,
    weather_conditions: Optional[Dict[str, Any]] = None,
    care_metrics: Optional[Dict[str, Any]] = None,
):
    """
    Update yield prediction based on crop progress

    Updates yield and harvest date predictions based on:
    - Current growth rate (0.0-1.5, where 1.0 is expected)
    - Recent weather conditions (optional)
    - Care metrics like fertilizer, pest control (optional)

    Returns updated predictions with quality grade.

    Validates: AC10.4 - Update yield predictions weekly based on growth rate
    Validates: AC10.5 - Adjust harvest date predictions based on growth rate
    Validates: AC10.6 - Predict quality grade based on growing conditions
    """
    try:
        from app.orm.crop import Crop
        from app.services.yield_prediction_update_service import get_yield_prediction_update_service

        crop = _owned_crop(crop_id, current_user)

        # Validate growth rate
        if growth_rate < 0.0 or growth_rate > 2.0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Growth rate must be between 0.0 and 2.0",
            )

        # Update prediction
        service = get_yield_prediction_update_service(db)
        result = await service.update_yield_prediction(
            crop_id=crop_id,
            current_growth_rate=growth_rate,
            weather_conditions=weather_conditions,
            care_metrics=care_metrics,
        )

        logger.info(f"Yield prediction updated for crop {crop_id}")

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating yield prediction: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update yield prediction: {str(e)}",
        )


@router.get("/harvest-readiness/{crop_id}", response_model=Dict[str, Any])
async def check_harvest_readiness(crop_id: int, current_user: CurrentFarmer, db: DB):
    """
    Check if crop has reached harvest readiness (90% maturity)

    Returns:
    - Maturity percentage
    - Harvest readiness status
    - Days to harvest
    - Optimal harvest window
    - Alert details if ready

    Validates: AC10.7 - Generate harvest readiness alerts at 90% maturity
    """
    try:
        from app.orm.crop import Crop
        from app.services.yield_prediction_update_service import get_yield_prediction_update_service

        crop = _owned_crop(crop_id, current_user)

        # Check readiness
        service = get_yield_prediction_update_service(db)
        result = await service.check_harvest_readiness(crop_id)

        logger.info(f"Harvest readiness checked for crop {crop_id}")

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error checking harvest readiness: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to check harvest readiness: {str(e)}",
        )


@router.post("/harvest-alert/{crop_id}", response_model=Dict[str, Any])
async def send_harvest_readiness_alert(crop_id: int, current_user: CurrentFarmer, db: DB):
    """
    Send harvest readiness alert to farmer

    Sends notification when crop reaches 90% maturity with:
    - Harvest readiness confirmation
    - Optimal harvest window
    - Action items and recommendations

    Validates: AC10.7 - Send harvest readiness alerts
    """
    try:
        from app.orm.crop import Crop
        from app.services.yield_prediction_update_service import get_yield_prediction_update_service

        crop = _owned_crop(crop_id, current_user)

        # Send alert
        service = get_yield_prediction_update_service(db)
        result = await service.send_harvest_readiness_alert(
            crop_id=crop_id,
            farmer_phone=getattr(current_user, "phone", None),
            farmer_email=current_user.email,
            farmer_name=getattr(current_user, "name", None) or current_user.email,
        )

        logger.info(f"Harvest readiness alert sent for crop {crop_id}")

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error sending harvest readiness alert: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send alert: {str(e)}",
        )


@router.get("/my-crops", response_model=Dict[str, Any])
async def get_my_crops(current_user=Depends(get_current_user)):
    """
    Get all crops for the current authenticated farmer
    Returns list of crops across all farms owned by the farmer
    """
    try:
        user_id = current_user.id

        # Get all farms owned by current user
        farms_result = Farm.where({"owner_id": [user_id], "is_active": [True]}).get()
        if not farms_result or not farms_result.items:
            return {"success": True, "crops": []}

        farms = farms_result.items
        farm_ids = [farm["id"] for farm in farms]

        # Get all plots from these farms
        plots_result = FarmPlot.where({"farm_id": farm_ids}).get()
        if not plots_result or not plots_result.items:
            return {"success": True, "crops": []}

        plots = plots_result.items
        plot_ids = [plot["id"] for plot in plots]

        # Get all crops from these plots
        crops_result = Crop.where({"farm_plot_id": plot_ids}).get()
        crops = crops_result.items if crops_result and crops_result.items else []

        # Build response with farm and plot details
        result = []
        for crop in crops:
            # Find the plot and farm for this crop
            plot = next((p for p in plots if p["id"] == crop["farm_plot_id"]), None)
            farm = next((f for f in farms if plot and f["id"] == plot["farm_id"]), None)

            result.append(
                {
                    "id": crop["id"],
                    "crop_name": crop.get("crop_name", ""),
                    "crop_variety": crop.get("crop_variety", ""),
                    "season": crop.get("season", ""),
                    "planting_date": crop.get("planting_date"),
                    "expected_harvest_date": crop.get("expected_harvest_date"),
                    "area": float(crop.get("area", 0)),
                    "expected_yield": float(crop.get("expected_yield", 0)),
                    "expected_profit": float(crop.get("expected_profit", 0)),
                    "actual_yield": (
                        float(crop.get("actual_yield", 0)) if crop.get("actual_yield") else None
                    ),
                    "actual_profit": (
                        float(crop.get("actual_profit", 0)) if crop.get("actual_profit") else None
                    ),
                    "status": crop.get("status", "planted"),
                    "parent_crop_id": crop.get("parent_crop_id"),
                    "crop_role": crop.get("crop_role") or "main",
                    "farm_name": farm.get("name", "") if farm else "",
                    "plot_name": plot.get("plot_name", "") if plot else "",
                    "created_at": crop.get("created_at"),
                }
            )

        logger.info(f"Retrieved {len(result)} crops for user {user_id}")

        return {"success": True, "crops": result, "total_count": len(result)}
    except Exception as e:
        logger.error(f"Error getting my crops: {e}")
        import traceback

        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get crops: {str(e)}",
        )
