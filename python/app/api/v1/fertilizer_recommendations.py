"""
Fertilizer Recommendation API endpoints
Handles fertilizer recommendations, application timing, and cost optimization

Task 24.1: Implement fertilizer recommendation engine
Validates: Requirements AC9 (Phase 6 - Required)
"""

import logging
from datetime import date
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.services.farm_access import farm_for_user, fetch_one, plot_for_user
from app.services.fertilizer_recommendation_service import fertilizer_service

logger = logging.getLogger(__name__)

from app.core.auth import get_current_active_user

router = APIRouter(
    prefix="/fertilizer-recommendations",
    tags=["fertilizer-recommendations"],
    dependencies=[Depends(get_current_active_user)],
)


def _owned(farm_id: int, plot_id: Optional[int], user) -> None:
    """Owner check (raw SQL via app.core.db.DB): farm must be the user's and the plot on it; 404 otherwise."""
    try:
        farm_for_user(farm_id, user)
        if plot_id is not None and plot_for_user(plot_id, user)["farm_id"] != farm_id:
            raise LookupError(f"Plot {plot_id} not found")
    except LookupError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


# Request/Response schemas
class FertilizerPlanRequest(BaseModel):
    """Request schema for complete fertilizer plan"""

    farm_id: int = Field(..., description="Farm ID")
    plot_id: Optional[int] = Field(None, description="Optional plot ID")
    crop_type: str = Field(..., description="Type of crop to be grown")
    area_hectares: float = Field(..., gt=0, description="Area in hectares")
    planting_date: date = Field(..., description="Planned or actual planting date")

    # Soil data (from latest soil test)
    soil_nitrogen_kg_per_ha: float = Field(0, ge=0, description="Current soil nitrogen (kg/ha)")
    soil_phosphorus_kg_per_ha: float = Field(0, ge=0, description="Current soil phosphorus (kg/ha)")
    soil_potassium_kg_per_ha: float = Field(0, ge=0, description="Current soil potassium (kg/ha)")
    soil_health_score: Optional[float] = Field(
        None, ge=0, le=100, description="Soil health score (0-100)"
    )

    # Preferences and constraints
    budget_per_hectare: Optional[float] = Field(
        None, gt=0, description="Budget constraint per hectare (₹)"
    )
    farmer_preference: str = Field(
        "balanced", description="Fertilizer preference: organic, chemical, or balanced"
    )
    target_yield_factor: float = Field(
        1.0, gt=0, le=2.0, description="Target yield multiplier (1.0 = normal)"
    )


class NutrientRequirementsRequest(BaseModel):
    """Request schema for nutrient requirements calculation"""

    crop_type: str = Field(..., description="Type of crop")
    area_hectares: float = Field(..., gt=0, description="Area in hectares")
    soil_nitrogen_kg_per_ha: float = Field(0, ge=0, description="Current soil nitrogen (kg/ha)")
    soil_phosphorus_kg_per_ha: float = Field(0, ge=0, description="Current soil phosphorus (kg/ha)")
    soil_potassium_kg_per_ha: float = Field(0, ge=0, description="Current soil potassium (kg/ha)")
    target_yield_factor: float = Field(1.0, gt=0, le=2.0, description="Target yield multiplier")


@router.get("", response_model=Dict[str, Any])
async def get_fertilizer_recommendations_root():
    """Registry alias for fertilizer recommendations root"""
    return {
        "status": "success",
        "message": "Fertilizer recommendation system operational",
        "features": ["complete_plan", "nutrient_requirements", "budget_optimization"],
    }


@router.post("/complete-plan", response_model=Dict[str, Any])
async def generate_complete_fertilizer_plan(
    request: FertilizerPlanRequest,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    """
    Generate complete fertilizer plan with recommendations, timing, and cost optimization

    This endpoint provides:
    - Nutrient requirement analysis (N, P, K)
    - Specific fertilizer recommendations (urea, DAP, MOP, organic)
    - Application timing based on crop growth stages
    - Organic vs chemical balancing
    - Cost optimization within budget
    """
    _owned(request.farm_id, request.plot_id, current_user)
    try:
        logger.info(
            f"Generating complete fertilizer plan for {request.crop_type} on farm {request.farm_id}"
        )

        # Prepare soil data
        soil_data = {
            "nitrogen_kg_per_ha": request.soil_nitrogen_kg_per_ha,
            "phosphorus_kg_per_ha": request.soil_phosphorus_kg_per_ha,
            "potassium_kg_per_ha": request.soil_potassium_kg_per_ha,
            "soil_health_score": request.soil_health_score or 60.0,
        }

        # If soil test data exists, fetch it
        if request.plot_id:
            soil_test = fetch_one(
                "SELECT * FROM soil_test_results WHERE plot_id = ? ORDER BY test_date DESC, id DESC LIMIT 1",
                [request.plot_id],
            )

            if soil_test:
                logger.info(f"Using soil test data from {soil_test.test_date}")
                soil_data = {
                    "nitrogen_kg_per_ha": (
                        float(soil_test.nitrogen_kg_per_ha) if soil_test.nitrogen_kg_per_ha else 0
                    ),
                    "phosphorus_kg_per_ha": (
                        float(soil_test.phosphorus_kg_per_ha)
                        if soil_test.phosphorus_kg_per_ha
                        else 0
                    ),
                    "potassium_kg_per_ha": (
                        float(soil_test.potassium_kg_per_ha) if soil_test.potassium_kg_per_ha else 0
                    ),
                    "soil_health_score": (
                        float(soil_test.soil_health_score) if soil_test.soil_health_score else 60.0
                    ),
                }

        # Generate complete plan
        plan = fertilizer_service.generate_complete_fertilizer_plan(
            crop_type=request.crop_type,
            area_hectares=request.area_hectares,
            soil_data=soil_data,
            planting_date=request.planting_date,
            budget_per_hectare=request.budget_per_hectare,
            farmer_preference=request.farmer_preference,
            target_yield_factor=request.target_yield_factor,
            weather_forecast=None,  # TODO: Integrate with weather service
        )

        # Convert dates to ISO format for JSON serialization
        plan["planting_date"] = plan["planting_date"].isoformat()
        for stage in plan["application_schedule"]["schedule"]:
            stage["date"] = stage["date"].isoformat()

        logger.info(
            f"Fertilizer plan generated successfully, total cost: ₹{plan['cost_summary']['total_cost']:.2f}"
        )

        return {"success": True, "message": "Fertilizer plan generated successfully", "plan": plan}

    except Exception as e:
        logger.error(f"Error generating fertilizer plan: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate fertilizer plan: {str(e)}",
        )


@router.post("/nutrient-requirements", response_model=Dict[str, Any])
async def calculate_nutrient_requirements(request: NutrientRequirementsRequest):
    """
    Calculate N, P, K requirements based on crop needs and soil deficiencies

    This endpoint analyzes:
    - Crop-specific nutrient requirements
    - Current soil nutrient levels
    - Nutrient deficits that need to be addressed
    """
    try:
        logger.info(f"Calculating nutrient requirements for {request.crop_type}")

        soil_data = {
            "nitrogen_kg_per_ha": request.soil_nitrogen_kg_per_ha,
            "phosphorus_kg_per_ha": request.soil_phosphorus_kg_per_ha,
            "potassium_kg_per_ha": request.soil_potassium_kg_per_ha,
        }

        requirements = fertilizer_service.calculate_nutrient_requirements(
            crop_type=request.crop_type,
            area_hectares=request.area_hectares,
            soil_data=soil_data,
            target_yield_factor=request.target_yield_factor,
        )

        return {
            "success": True,
            "message": "Nutrient requirements calculated successfully",
            "requirements": requirements,
        }

    except Exception as e:
        logger.error(f"Error calculating nutrient requirements: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to calculate nutrient requirements: {str(e)}",
        )


@router.get("/fertilizer-types", response_model=Dict[str, Any])
async def get_fertilizer_types():
    """
    Get available fertilizer types with nutrient content and costs

    Returns information about:
    - Chemical fertilizers (urea, DAP, MOP, etc.)
    - Organic fertilizers (vermicompost, FYM, etc.)
    - Nutrient content percentages
    - Cost per kg
    """
    try:
        fertilizer_types = fertilizer_service.FERTILIZER_TYPES

        # Group by type
        chemical = {k: v for k, v in fertilizer_types.items() if v["type"] == "chemical"}
        organic = {k: v for k, v in fertilizer_types.items() if v["type"] == "organic"}

        return {
            "success": True,
            "fertilizer_types": {"chemical": chemical, "organic": organic, "all": fertilizer_types},
        }

    except Exception as e:
        logger.error(f"Error fetching fertilizer types: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch fertilizer types",
        )


@router.get("/crop-requirements", response_model=Dict[str, Any])
async def get_crop_nutrient_requirements(
    crop_type: Optional[str] = Query(None, description="Specific crop type (optional)")
):
    """
    Get standard nutrient requirements for crops

    Returns N, P, K requirements per hectare for different crops
    """
    try:
        requirements = fertilizer_service.CROP_NUTRIENT_REQUIREMENTS

        if crop_type:
            crop_key = crop_type.lower().replace(" ", "_")
            crop_req = requirements.get(crop_key, requirements["default"])
            return {"success": True, "crop_type": crop_type, "requirements": crop_req}
        else:
            return {"success": True, "all_crops": requirements}

    except Exception as e:
        logger.error(f"Error fetching crop requirements: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch crop requirements",
        )


@router.post("/optimize-budget", response_model=Dict[str, Any])
async def optimize_fertilizer_for_budget(
    request: NutrientRequirementsRequest,
    budget_per_hectare: float = Query(..., gt=0, description="Budget per hectare (₹)"),
    min_organic_ratio: float = Query(0.2, ge=0, le=1, description="Minimum organic ratio (0-1)"),
):
    """
    Generate cost-optimized fertilizer plan within budget constraints

    This endpoint:
    - Optimizes fertilizer selection to fit budget
    - Maintains minimum organic fertilizer ratio
    - Maximizes nutrient delivery within cost constraints
    """
    try:
        logger.info(f"Optimizing fertilizer plan for budget: ₹{budget_per_hectare}/ha")

        soil_data = {
            "nitrogen_kg_per_ha": request.soil_nitrogen_kg_per_ha,
            "phosphorus_kg_per_ha": request.soil_phosphorus_kg_per_ha,
            "potassium_kg_per_ha": request.soil_potassium_kg_per_ha,
        }

        # Calculate requirements
        nutrient_req = fertilizer_service.calculate_nutrient_requirements(
            crop_type=request.crop_type,
            area_hectares=request.area_hectares,
            soil_data=soil_data,
            target_yield_factor=request.target_yield_factor,
        )

        # Optimize for budget
        optimized_plan = fertilizer_service.optimize_for_budget(
            nutrient_requirements=nutrient_req,
            budget_per_hectare=budget_per_hectare,
            min_organic_ratio=min_organic_ratio,
        )

        return {
            "success": True,
            "message": "Budget-optimized plan generated successfully",
            "plan": optimized_plan,
            "nutrient_requirements": nutrient_req,
        }

    except Exception as e:
        logger.error(f"Error optimizing for budget: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to optimize fertilizer plan: {str(e)}",
        )


@router.get("/farm/{farm_id}/recommendations", response_model=Dict[str, Any])
async def get_farm_fertilizer_recommendations(
    farm_id: int,
    plot_id: Optional[int] = Query(None, description="Optional plot ID"),
    crop_type: str = Query(..., description="Crop type"),
    area_hectares: float = Query(..., gt=0, description="Area in hectares"),
    planting_date: date = Query(..., description="Planting date"),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    """
    Get fertilizer recommendations for a specific farm using latest soil test data

    This endpoint automatically fetches the latest soil test results for the farm/plot
    and generates appropriate fertilizer recommendations.
    """
    _owned(farm_id, plot_id, current_user)
    try:
        logger.info(f"Fetching fertilizer recommendations for farm {farm_id}")

        # Fetch latest soil test
        sql, bind = "SELECT * FROM soil_test_results WHERE farm_id = ?", [farm_id]
        if plot_id:
            sql += " AND plot_id = ?"
            bind.append(plot_id)
        soil_test = fetch_one(sql + " ORDER BY test_date DESC, id DESC LIMIT 1", bind)

        if not soil_test:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No soil test results found for this farm. Please upload soil test data first.",
            )

        # Prepare soil data
        soil_data = {
            "nitrogen_kg_per_ha": (
                float(soil_test.nitrogen_kg_per_ha) if soil_test.nitrogen_kg_per_ha else 0
            ),
            "phosphorus_kg_per_ha": (
                float(soil_test.phosphorus_kg_per_ha) if soil_test.phosphorus_kg_per_ha else 0
            ),
            "potassium_kg_per_ha": (
                float(soil_test.potassium_kg_per_ha) if soil_test.potassium_kg_per_ha else 0
            ),
            "soil_health_score": (
                float(soil_test.soil_health_score) if soil_test.soil_health_score else 60.0
            ),
        }

        # Generate plan
        plan = fertilizer_service.generate_complete_fertilizer_plan(
            crop_type=crop_type,
            area_hectares=area_hectares,
            soil_data=soil_data,
            planting_date=planting_date,
            budget_per_hectare=None,
            farmer_preference="balanced",
            target_yield_factor=1.0,
            weather_forecast=None,
        )

        # Convert dates to ISO format
        plan["planting_date"] = plan["planting_date"].isoformat()
        for stage in plan["application_schedule"]["schedule"]:
            stage["date"] = stage["date"].isoformat()

        return {
            "success": True,
            "message": "Fertilizer recommendations generated successfully",
            "soil_test_date": soil_test.test_date.isoformat(),
            "soil_test_id": soil_test.id,
            "plan": plan,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching farm recommendations: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate recommendations: {str(e)}",
        )
