"""
Livestock Management API Endpoints
Handles livestock registration, profile management, and portfolio dashboard
"""

import logging
from datetime import datetime
from decimal import Decimal
from typing import Annotated, Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import DB, CurrentFarmer, LivestockSvc, MarketplaceSvc
from app.orm.livestock import Livestock
from app.schemas.livestock import (
    LivestockCreate,
    LivestockPortfolioDashboard,
    LivestockResponse,
    LivestockUpdate,
    LivestockWithROI,
)
from app.services.livestock_roi_service import get_roi_calculator

logger = logging.getLogger(__name__)

from app.core.auth import get_current_active_user

router = APIRouter(
    prefix="/livestock", tags=["livestock"], dependencies=[Depends(get_current_active_user)]
)


@router.post("", response_model=Dict[str, Any], status_code=status.HTTP_201_CREATED)
async def create_livestock(
    request: LivestockCreate, current_user: CurrentFarmer, db: DB, service: LivestockSvc
):
    """
    Register new livestock

    Creates a new livestock record with species, breed, age, purchase details, and purpose.
    Automatically calculates expected ROI and break-even date.
    """
    try:
        # Create livestock record
        livestock_data = request.model_dump()

        # Calculate ROI and break-even date
        roi_calculator = get_roi_calculator()

        # Calculate age in months from purchase date
        purchase_date = livestock_data["purchase_date"]
        current_age_months = (datetime.now().date() - purchase_date).days // 30

        # Calculate ROI metrics
        roi_metrics = roi_calculator.calculate_roi(
            species=livestock_data["species"],
            purpose=livestock_data["purpose"],
            purchase_price=float(livestock_data["purchase_price"]),
            current_age_months=max(1, current_age_months),
            total_investment=float(livestock_data["purchase_price"]),
            total_revenue=0.0,
            milk_production_liters_per_day=None,
        )

        # Set expected ROI and break-even date
        livestock_data["expected_roi"] = Decimal(str(roi_metrics["projected_annual_profit"]))
        if roi_metrics["break_even_date"]:
            livestock_data["break_even_date"] = datetime.strptime(
                roi_metrics["break_even_date"], "%Y-%m-%d"
            ).date()

        # Create livestock in database
        result = service.create(livestock_data)

        logger.info(
            f"Created livestock: {result['id']} - {livestock_data['species']} ({livestock_data['breed']})"
        )

        return LivestockResponse(**result)

    except Exception as e:
        logger.error(f"Error creating livestock: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create livestock: {str(e)}",
        )


@router.get("/{id}", response_model=LivestockWithROI)
def get_livestock(
    id: int,
    db: DB,
    service: LivestockSvc,
    include_roi: bool = Query(True, description="Include ROI calculations"),
):
    """
    Get livestock by ID with optional ROI metrics
    """
    try:
        livestock = service.get_by_id(id)

        if not livestock:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Livestock not found")

        response_data = LivestockResponse(**livestock)

        # Calculate ROI metrics if requested
        if include_roi:
            roi_calculator = get_roi_calculator()

            # Calculate age in months
            purchase_date = livestock["purchase_date"]
            current_age_months = (datetime.now().date() - purchase_date).days // 30

            # Calculate ROI
            roi_metrics = roi_calculator.calculate_roi(
                species=livestock["species"],
                purpose=livestock["purpose"],
                purchase_price=float(livestock["purchase_price"]),
                current_age_months=max(1, current_age_months),
                total_investment=float(livestock["purchase_price"]),
                total_revenue=0.0,
                milk_production_liters_per_day=None,
            )

            return LivestockWithROI(**response_data.model_dump(), roi_metrics=roi_metrics)

        return LivestockWithROI(**response_data.model_dump())

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching livestock {id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch livestock: {str(e)}",
        )


@router.get("/", response_model=List[LivestockResponse])
def list_livestock(
    db: DB,
    service: LivestockSvc,
    farmer_id: Optional[int] = Query(None, description="Filter by farmer ID"),
    farm_id: Optional[int] = Query(None, description="Filter by farm ID"),
    species: Optional[str] = Query(None, description="Filter by species"),
    purpose: Optional[str] = Query(None, description="Filter by purpose"),
    status_filter: str = Query("active", description="Filter by status", alias="status"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
):
    """
    List livestock with optional filters
    """
    try:
        # Build filter conditions
        conditions = {}
        if farmer_id:
            conditions["farmer_id"] = farmer_id
        if farm_id:
            conditions["farm_id"] = farm_id
        if species:
            conditions["species"] = species.lower()
        if purpose:
            conditions["purpose"] = purpose.lower()
        if status_filter:
            conditions["status"] = status_filter.lower()

        # Get livestock list
        livestock_list = service.list(conditions=conditions, skip=skip, limit=limit)

        return [LivestockResponse(**item) for item in livestock_list]

    except Exception as e:
        logger.error(f"Error listing livestock: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list livestock: {str(e)}",
        )


@router.put("/{id}", response_model=LivestockResponse)
def update_livestock(id: int, livestock: LivestockUpdate, db: DB, service: LivestockSvc):
    """
    Update livestock profile

    Allows editing livestock details including species, breed, purchase info, and status.
    Recalculates ROI if relevant fields are updated.
    """
    try:
        # Check if livestock exists
        existing = service.get_by_id(id)
        if not existing:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Livestock not found")

        # Update livestock
        update_data = livestock.model_dump(exclude_unset=True)

        # Recalculate ROI if relevant fields changed
        if any(
            key in update_data for key in ["species", "purpose", "purchase_price", "purchase_date"]
        ):
            roi_calculator = get_roi_calculator()

            # Merge with existing data
            merged_data = {**existing, **update_data}

            # Calculate age in months
            purchase_date = merged_data["purchase_date"]
            current_age_months = (datetime.now().date() - purchase_date).days // 30

            # Calculate ROI
            roi_metrics = roi_calculator.calculate_roi(
                species=merged_data["species"],
                purpose=merged_data["purpose"],
                purchase_price=float(merged_data["purchase_price"]),
                current_age_months=max(1, current_age_months),
                total_investment=float(merged_data["purchase_price"]),
                total_revenue=0.0,
                milk_production_liters_per_day=None,
            )

            # Update ROI fields
            update_data["expected_roi"] = Decimal(str(roi_metrics["projected_annual_profit"]))
            if roi_metrics["break_even_date"]:
                update_data["break_even_date"] = datetime.strptime(
                    roi_metrics["break_even_date"], "%Y-%m-%d"
                ).date()

        result = service.update(id, update_data)

        if not result:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Livestock not found")

        logger.info(f"Updated livestock: {id}")

        return LivestockResponse(**result)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating livestock {id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update livestock: {str(e)}",
        )


@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_livestock(id: int, db: DB, service: LivestockSvc):
    """
    Delete livestock (soft delete by setting enable=0)
    """
    try:
        success = service.delete(id)

        if not success:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Livestock not found")

        logger.info(f"Deleted livestock: {id}")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting livestock {id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete livestock: {str(e)}",
        )


@router.get("/farmer/{farmer_id}/portfolio", response_model=LivestockPortfolioDashboard)
def get_livestock_portfolio(farmer_id: int, db: DB, service: LivestockSvc):
    """
    Generate livestock portfolio dashboard

    Provides comprehensive overview of farmer's livestock portfolio including:
    - Total investment and expected returns
    - ROI analysis by species and purpose
    - Break-even status summary
    - Active livestock count
    """
    try:
        roi_calculator = get_roi_calculator()

        # Get all active livestock for farmer
        livestock_list = service.list(
            conditions={"farmer_id": farmer_id, "status": "active"}, skip=0, limit=1000
        )

        if not livestock_list:
            return LivestockPortfolioDashboard(
                total_livestock=0,
                total_investment=Decimal("0"),
                total_expected_returns=Decimal("0"),
                total_current_value=Decimal("0"),
                overall_roi_percentage=Decimal("0"),
                livestock_by_species={},
                livestock_by_purpose={},
                active_livestock=0,
                break_even_summary={"achieved": 0, "pending": 0},
            )

        # Calculate portfolio metrics
        total_investment = Decimal("0")
        total_expected_returns = Decimal("0")
        livestock_by_species = {}
        livestock_by_purpose = {}
        break_even_achieved = 0
        break_even_pending = 0

        for livestock in livestock_list:
            # Add to investment
            investment = Decimal(str(livestock["purchase_price"])) * livestock["quantity"]
            total_investment += investment

            # Calculate expected returns
            if livestock["expected_roi"]:
                total_expected_returns += (
                    Decimal(str(livestock["expected_roi"])) * livestock["quantity"]
                )

            # Group by species
            species = livestock["species"]
            if species not in livestock_by_species:
                livestock_by_species[species] = {
                    "count": 0,
                    "investment": Decimal("0"),
                    "expected_returns": Decimal("0"),
                }
            livestock_by_species[species]["count"] += livestock["quantity"]
            livestock_by_species[species]["investment"] += investment
            if livestock["expected_roi"]:
                livestock_by_species[species]["expected_returns"] += (
                    Decimal(str(livestock["expected_roi"])) * livestock["quantity"]
                )

            # Group by purpose
            purpose = livestock["purpose"]
            if purpose not in livestock_by_purpose:
                livestock_by_purpose[purpose] = {
                    "count": 0,
                    "investment": Decimal("0"),
                    "expected_returns": Decimal("0"),
                }
            livestock_by_purpose[purpose]["count"] += livestock["quantity"]
            livestock_by_purpose[purpose]["investment"] += investment
            if livestock["expected_roi"]:
                livestock_by_purpose[purpose]["expected_returns"] += (
                    Decimal(str(livestock["expected_roi"])) * livestock["quantity"]
                )

            # Break-even status
            if livestock["break_even_date"]:
                if livestock["break_even_date"] <= datetime.now().date():
                    break_even_achieved += livestock["quantity"]
                else:
                    break_even_pending += livestock["quantity"]
            else:
                break_even_pending += livestock["quantity"]

        # Calculate overall ROI
        total_current_value = total_investment + total_expected_returns
        overall_roi_percentage = Decimal("0")
        if total_investment > 0:
            overall_roi_percentage = ((total_expected_returns / total_investment) * 100).quantize(
                Decimal("0.01")
            )

        # Convert Decimal to float for JSON serialization
        livestock_by_species_serializable = {
            k: {
                "count": v["count"],
                "investment": float(v["investment"]),
                "expected_returns": float(v["expected_returns"]),
            }
            for k, v in livestock_by_species.items()
        }

        livestock_by_purpose_serializable = {
            k: {
                "count": v["count"],
                "investment": float(v["investment"]),
                "expected_returns": float(v["expected_returns"]),
            }
            for k, v in livestock_by_purpose.items()
        }

        return LivestockPortfolioDashboard(
            total_livestock=sum(l["quantity"] for l in livestock_list),
            total_investment=total_investment,
            total_expected_returns=total_expected_returns,
            total_current_value=total_current_value,
            overall_roi_percentage=overall_roi_percentage,
            livestock_by_species=livestock_by_species_serializable,
            livestock_by_purpose=livestock_by_purpose_serializable,
            active_livestock=len(livestock_list),
            break_even_summary={"achieved": break_even_achieved, "pending": break_even_pending},
        )

    except Exception as e:
        logger.error(f"Error generating portfolio for farmer {farmer_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate portfolio: {str(e)}",
        )


@router.get("/{id}/roi-report")
def get_roi_report(id: int, db: DB, service: LivestockSvc):
    """
    Generate comprehensive ROI report for specific livestock

    Includes:
    - Break-even timeline calculation (within 30 days accuracy)
    - Projected returns for 1, 2, and 5 year periods
    - Investment vs return analysis with ROI percentages
    - Confidence intervals for projections
    """
    try:
        livestock = service.get_by_id(id)

        if not livestock:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Livestock not found")

        roi_calculator = get_roi_calculator()

        # Calculate age in months
        purchase_date = livestock["purchase_date"]
        current_age_months = (datetime.now().date() - purchase_date).days // 30

        # Calculate current ROI metrics
        roi_metrics = roi_calculator.calculate_roi(
            species=livestock["species"],
            purpose=livestock["purpose"],
            purchase_price=float(livestock["purchase_price"]),
            current_age_months=max(1, current_age_months),
            total_investment=float(livestock["purchase_price"]),
            total_revenue=0.0,
            milk_production_liters_per_day=None,
        )

        # Generate comprehensive report
        livestock_data = {
            "species": livestock["species"],
            "breed": livestock["breed"],
            "purpose": livestock["purpose"],
            "purchase_price": float(livestock["purchase_price"]),
            "current_age_months": max(1, current_age_months),
            "milk_production_liters_per_day": None,
        }

        report = roi_calculator.generate_roi_report(livestock_data, roi_metrics)

        logger.info(f"Generated ROI report for livestock: {id}")

        return report

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating ROI report for livestock {id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate ROI report: {str(e)}",
        )


@router.post("/compare-options")
def compare_livestock_options(options: List[Dict[str, Any]], db: Session = Depends(get_db)):
    """
    Compare ROI across different livestock options

    Helps farmers make informed purchase decisions by comparing:
    - Break-even timelines
    - Projected returns (1, 2, 5 years)
    - ROI percentages
    - Monthly cash flow

    Request body should be a list of livestock options with:
    - species: str (cattle, buffalo, goat, poultry)
    - breed: str
    - purpose: str (dairy, meat, breeding, eggs)
    - purchase_price: float
    - age_months: int
    - milk_production_liters_per_day: float (optional, for dairy)
    """
    try:
        roi_calculator = get_roi_calculator()

        comparison = roi_calculator.compare_livestock_options(options)

        logger.info(f"Compared {len(options)} livestock options")

        return comparison

    except Exception as e:
        logger.error(f"Error comparing livestock options: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to compare options: {str(e)}",
        )
