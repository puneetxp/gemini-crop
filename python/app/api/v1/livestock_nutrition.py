"""
Livestock Nutrition Advisor API Endpoints
AI-powered nutrition recommendations and feed optimization

Task 28.1: Implement AI-powered nutrition advisor
"""

import logging
from datetime import date, datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services.livestock_nutrition_service import nutrition_service
from app.services.livestock_service import get_service as get_livestock_service

logger = logging.getLogger(__name__)

from app.core.auth import get_current_active_user

router = APIRouter(
    prefix="/livestock-nutrition",
    tags=["livestock-nutrition"],
    dependencies=[Depends(get_current_active_user)],
)
# Request/Response Schemas


class FeedingRecommendationRequest(BaseModel):
    """Request schema for feeding recommendations"""

    species: str = Field(..., description="Livestock species (cattle, buffalo, goat, poultry)")
    breed: str = Field(..., description="Breed name")
    age_months: int = Field(..., ge=0, description="Age in months")
    weight_kg: float = Field(..., gt=0, description="Current weight in kg")
    purpose: str = Field(..., description="Purpose (dairy, meat, breeding, eggs)")
    lactation_status: Optional[str] = Field(
        None, description="For dairy: dry, early_lactation, peak_lactation, late_lactation"
    )
    milk_production_liters: Optional[float] = Field(
        None, ge=0, description="Current milk production per day"
    )
    location_state: Optional[str] = Field(None, description="State for regional feed availability")


class FeedIngredient(BaseModel):
    """Feed ingredient with price"""

    name: str = Field(..., description="Ingredient name")
    price_per_kg: float = Field(..., ge=0, description="Price per kg in INR")
    protein_percentage: float = Field(..., ge=0, le=100, description="Protein content percentage")
    energy_mj_per_kg: float = Field(..., ge=0, description="Energy content in MJ per kg")
    locally_available: bool = Field(True, description="Whether ingredient is locally available")


class FeedOptimizationRequest(BaseModel):
    """Request schema for feed cost optimization"""

    species: str = Field(..., description="Livestock species")
    weight_kg: float = Field(..., gt=0, description="Current weight in kg")
    purpose: str = Field(..., description="Purpose (dairy, meat, breeding, eggs)")
    nutritional_requirements: Dict[str, Any] = Field(..., description="Required nutrients")
    available_feeds: List[FeedIngredient] = Field(
        ..., description="Available feed ingredients with prices"
    )
    location_state: Optional[str] = Field(None, description="State for regional feed availability")


class GrowthStagePlanRequest(BaseModel):
    """Request schema for growth stage nutrition plan"""

    species: str = Field(..., description="Livestock species")
    breed: str = Field(..., description="Breed name")
    purpose: str = Field(..., description="Purpose (dairy, meat, breeding, eggs)")
    current_age_months: int = Field(..., ge=0, description="Current age in months")
    current_weight_kg: float = Field(..., gt=0, description="Current weight in kg")
    target_weight_kg: Optional[float] = Field(
        None, gt=0, description="Target weight for meat animals"
    )


class FeedEfficiencyReportRequest(BaseModel):
    """Request schema for feed efficiency report"""

    livestock_id: int = Field(..., description="Livestock ID")
    start_weight_kg: float = Field(..., gt=0, description="Starting weight in kg")
    current_weight_kg: float = Field(..., gt=0, description="Current weight in kg")
    days_elapsed: int = Field(..., gt=0, description="Days since start")
    total_feed_cost_inr: float = Field(..., ge=0, description="Total feed cost in INR")
    milk_production_liters: Optional[float] = Field(
        None, ge=0, description="Average daily milk production"
    )


# API Endpoints


@router.get("/{id}")
def get_nutrition_summary_alias(
    id: int, db: Session = Depends(get_db), current_user=Depends(get_current_active_user)
):
    """Registry alias for nutrition summary"""
    return get_livestock_nutrition_summary(id, db, current_user)


@router.post("/feeding-recommendations")
def get_feeding_recommendations(
    request: FeedingRecommendationRequest, db: Session = Depends(get_db)
):
    """
    Get personalized feeding recommendations using AI

    Provides comprehensive feeding recommendations based on livestock type, age, purpose, and weight.
    Includes daily nutritional requirements, feed composition, feeding schedule, and cost estimation.

    **Features:**
    - Personalized for specific livestock characteristics
    - Growth stage-specific recommendations
    - Regional feed availability consideration
    - Cost estimation for budgeting
    - Cached for 6 hours to reduce API costs
    """
    try:
        recommendations = nutrition_service.get_feeding_recommendations(
            species=request.species,
            breed=request.breed,
            age_months=request.age_months,
            weight_kg=request.weight_kg,
            purpose=request.purpose,
            lactation_status=request.lactation_status,
            milk_production_liters=request.milk_production_liters,
            location_state=request.location_state,
        )

        logger.info(f"Generated feeding recommendations for {request.species} ({request.breed})")

        return {
            "success": True,
            "data": recommendations,
            "message": "Feeding recommendations generated successfully",
        }

    except Exception as e:
        logger.error(f"Error generating feeding recommendations: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate feeding recommendations: {str(e)}",
        )


@router.post("/optimize-feed-cost")
def optimize_feed_cost(request: FeedOptimizationRequest, db: Session = Depends(get_db)):
    """
    Optimize feed composition to meet nutritional requirements at minimum cost

    Uses AI to create an optimized feed plan that meets all nutritional requirements
    while minimizing total feed cost. Considers locally available ingredients and
    practical feeding implementation.

    **Features:**
    - Meets all nutritional requirements
    - Minimizes total feed cost
    - Uses locally available ingredients
    - Provides alternative options
    - Shows cost savings vs standard feeding
    """
    try:
        # Convert FeedIngredient models to dicts
        available_feeds = [
            {
                "name": feed.name,
                "price_per_kg": feed.price_per_kg,
                "protein_percentage": feed.protein_percentage,
                "energy_mj_per_kg": feed.energy_mj_per_kg,
                "locally_available": feed.locally_available,
            }
            for feed in request.available_feeds
        ]

        optimization = nutrition_service.optimize_feed_cost(
            species=request.species,
            weight_kg=request.weight_kg,
            purpose=request.purpose,
            nutritional_requirements=request.nutritional_requirements,
            available_feeds=available_feeds,
            location_state=request.location_state,
        )

        logger.info(f"Generated feed cost optimization for {request.species}")

        return {
            "success": True,
            "data": optimization,
            "message": "Feed cost optimization completed successfully",
        }

    except Exception as e:
        logger.error(f"Error optimizing feed cost: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to optimize feed cost: {str(e)}",
        )


@router.post("/growth-stage-plan")
def get_growth_stage_plan(request: GrowthStagePlanRequest, db: Session = Depends(get_db)):
    """
    Get nutritional planning for different growth stages

    Provides comprehensive nutrition plan across all growth stages from calf/young
    to adult, including special stages like pregnancy and lactation. Helps farmers
    plan long-term nutrition and budget for livestock development.

    **Features:**
    - Stage-specific nutritional requirements
    - Feed composition for each stage
    - Cost estimation per stage
    - Transition guidelines between stages
    - Total cost to maturity calculation
    """
    try:
        plan = nutrition_service.get_growth_stage_nutrition_plan(
            species=request.species,
            breed=request.breed,
            purpose=request.purpose,
            current_age_months=request.current_age_months,
            current_weight_kg=request.current_weight_kg,
            target_weight_kg=request.target_weight_kg,
        )

        logger.info(f"Generated growth stage plan for {request.species} ({request.breed})")

        return {
            "success": True,
            "data": plan,
            "message": "Growth stage nutrition plan generated successfully",
        }

    except Exception as e:
        logger.error(f"Error generating growth stage plan: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate growth stage plan: {str(e)}",
        )


@router.post("/feed-efficiency-report")
def generate_feed_efficiency_report(
    request: FeedEfficiencyReportRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    """
    Generate feed efficiency report with cost per kg gain

    Analyzes livestock performance and feed efficiency, providing detailed metrics
    including cost per kg gain, feed conversion ratio, and recommendations for
    improvement. Compares performance against industry benchmarks.

    **Features:**
    - Feed efficiency metrics (FCR, daily gain, cost per kg)
    - Performance benchmarking against industry standards
    - Cost efficiency analysis
    - Actionable recommendations for improvement
    - Projected improvements with timeline
    """
    try:
        # Get livestock details
        livestock_service = get_livestock_service()
        livestock = livestock_service.find(request.livestock_id, owner=current_user)

        if not livestock:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Livestock not found")

        report = nutrition_service.generate_feed_efficiency_report(
            livestock_id=request.livestock_id,
            species=livestock["species"],
            purpose=livestock["purpose"],
            start_weight_kg=request.start_weight_kg,
            current_weight_kg=request.current_weight_kg,
            days_elapsed=request.days_elapsed,
            total_feed_cost_inr=request.total_feed_cost_inr,
            milk_production_liters=request.milk_production_liters,
        )

        logger.info(f"Generated feed efficiency report for livestock {request.livestock_id}")

        return {
            "success": True,
            "data": report,
            "message": "Feed efficiency report generated successfully",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating feed efficiency report: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate feed efficiency report: {str(e)}",
        )


@router.get("/livestock/{livestock_id}/nutrition-summary")
def get_livestock_nutrition_summary(
    livestock_id: int, db: Session = Depends(get_db), current_user=Depends(get_current_active_user)
):
    """
    Get comprehensive nutrition summary for specific livestock

    Provides a complete nutrition overview including current feeding recommendations,
    growth stage information, and feed efficiency metrics (if available).

    **Returns:**
    - Current feeding recommendations
    - Growth stage information
    - Nutritional requirements
    - Cost estimation
    """
    try:
        # Get livestock details
        livestock_service = get_livestock_service()
        livestock = livestock_service.find(livestock_id, owner=current_user)

        if not livestock:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Livestock not found")

        # Calculate age in months
        purchase_date = livestock["purchase_date"]
        current_age_months = (datetime.now().date() - purchase_date).days // 30

        # Estimate weight (simple estimation, should be tracked separately in production)
        # For cattle: ~25kg at birth, ~0.5kg/day gain
        estimated_weight = 25 + (current_age_months * 30 * 0.5)

        # Get feeding recommendations
        recommendations = nutrition_service.get_feeding_recommendations(
            species=livestock["species"],
            breed=livestock["breed"],
            age_months=max(1, current_age_months),
            weight_kg=estimated_weight,
            purpose=livestock["purpose"],
            lactation_status=None,
            milk_production_liters=None,
            location_state=None,
        )

        logger.info(f"Generated nutrition summary for livestock {livestock_id}")

        return {
            "success": True,
            "data": {
                "livestock_id": livestock_id,
                "species": livestock["species"],
                "breed": livestock["breed"],
                "age_months": current_age_months,
                "estimated_weight_kg": estimated_weight,
                "purpose": livestock["purpose"],
                "feeding_recommendations": recommendations,
            },
            "message": "Nutrition summary generated successfully",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating nutrition summary for livestock {livestock_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate nutrition summary: {str(e)}",
        )


@router.get("/feed-ingredients/regional")
def get_regional_feed_ingredients(
    state: str = Query(..., description="State name"),
    species: str = Query(..., description="Livestock species"),
    db: Session = Depends(get_db),
):
    """
    Get list of commonly available feed ingredients for a region

    Provides information about locally available feed ingredients including
    typical prices and nutritional content. Helps farmers plan feed procurement.

    **Note:** This is a placeholder endpoint. In production, this would query
    a database of regional feed prices and availability.
    """
    try:
        # Placeholder data - in production, this would query a database
        common_feeds = {
            "cattle": [
                {
                    "name": "Green Maize Fodder",
                    "price_per_kg": 2.0,
                    "protein_percentage": 2.5,
                    "energy_mj_per_kg": 2.8,
                    "locally_available": True,
                },
                {
                    "name": "Wheat Straw",
                    "price_per_kg": 3.0,
                    "protein_percentage": 3.5,
                    "energy_mj_per_kg": 6.5,
                    "locally_available": True,
                },
                {
                    "name": "Cotton Seed Cake",
                    "price_per_kg": 25.0,
                    "protein_percentage": 22.0,
                    "energy_mj_per_kg": 11.0,
                    "locally_available": True,
                },
                {
                    "name": "Wheat Bran",
                    "price_per_kg": 15.0,
                    "protein_percentage": 15.0,
                    "energy_mj_per_kg": 10.5,
                    "locally_available": True,
                },
                {
                    "name": "Mineral Mixture",
                    "price_per_kg": 40.0,
                    "protein_percentage": 0.0,
                    "energy_mj_per_kg": 0.0,
                    "locally_available": True,
                },
            ],
            "goat": [
                {
                    "name": "Green Grass",
                    "price_per_kg": 1.5,
                    "protein_percentage": 3.0,
                    "energy_mj_per_kg": 2.5,
                    "locally_available": True,
                },
                {
                    "name": "Groundnut Cake",
                    "price_per_kg": 30.0,
                    "protein_percentage": 45.0,
                    "energy_mj_per_kg": 12.0,
                    "locally_available": True,
                },
            ],
            "poultry": [
                {
                    "name": "Maize Grain",
                    "price_per_kg": 20.0,
                    "protein_percentage": 9.0,
                    "energy_mj_per_kg": 14.0,
                    "locally_available": True,
                },
                {
                    "name": "Soybean Meal",
                    "price_per_kg": 35.0,
                    "protein_percentage": 44.0,
                    "energy_mj_per_kg": 10.0,
                    "locally_available": True,
                },
            ],
        }

        feeds = common_feeds.get(species.lower(), common_feeds["cattle"])

        logger.info(f"Retrieved regional feed ingredients for {state}, {species}")

        return {
            "success": True,
            "data": {
                "state": state,
                "species": species,
                "feed_ingredients": feeds,
                "note": "Prices are approximate and may vary by location and season",
            },
            "message": "Regional feed ingredients retrieved successfully",
        }

    except Exception as e:
        logger.error(f"Error retrieving regional feed ingredients: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve feed ingredients: {str(e)}",
        )
