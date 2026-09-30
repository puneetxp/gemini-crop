"""
Soil Health Management API endpoints
Handles soil tests, fertilizer applications, and soil amendments
"""

import logging
from datetime import datetime, timedelta
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import and_, func
from sqlalchemy.orm import Session

from app.core.dependencies import DB, CurrentFarmer
from app.models.soil_health import FertilizerApplication, SoilAmendment, SoilTest
from app.orm.farm import Farm
from app.orm.farm_plot import FarmPlot
from app.orm.user import User
from app.schemas.auth import MessageResponse
from app.schemas.soil import (
    FertilizerApplicationCreate,
    FertilizerApplicationResponse,
    FertilizerApplicationUpdate,
    SoilAmendmentCreate,
    SoilAmendmentResponse,
    SoilAmendmentUpdate,
    SoilHealthSummary,
    SoilTestCreate,
    SoilTestResponse,
    SoilTestUpdate,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/soil", tags=["soil"])


@router.get("/recommendations", response_model=List[dict])
async def get_soil_recommendations_alias(plot_id: int, db: DB):
    """Registry alias for soil recommendations"""
    # Using existing logic from get_plot_soil_health_summary but focused on recommendations
    from app.services.soil_testing_service import soil_testing_service

    action_plan = await soil_testing_service.generate_improvement_action_plan(db, plot_id=plot_id)
    return action_plan.get("immediate_actions", [])


@router.get("/moisture")
async def get_soil_moisture(
    state: str = Query(..., description="State name"),
    district: str = Query(..., description="District name"),
    limit: int = Query(10, ge=1, le=100, description="Limit records"),
):
    """
    Get latest soil moisture records for a given state and district
    """
    from app.orm.soil_moisture_data import SoilMoistureData

    # Query database for moisture records
    records = SoilMoistureData.where({"state": state, "district": district}).paginate(1, limit)

    data = []
    if records and records.items:
        data = records.items

    return {"success": True, "state": state, "district": district, "data": data}


def verify_plot_ownership(plot_id: int, user_id: int, db: Session) -> FarmPlot:
    """Verify that the user owns the plot"""
    plot = db.query(FarmPlot).filter(FarmPlot.id == plot_id).first()

    if not plot:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Plot not found")

    # Check farm ownership
    farm = db.query(Farm).filter(Farm.id == plot.farm_id).first()
    if not farm or farm.farmer_id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    return plot


# Soil Test Endpoints


@router.post("/tests", response_model=SoilTestResponse, status_code=status.HTTP_201_CREATED)
async def create_soil_test(test_data: SoilTestCreate, current_user: CurrentFarmer, db: DB):
    """
    Record a new soil test result

    - **plot_id**: Plot ID
    - **test_date**: Date of soil test
    - **ph_level**: Soil pH level (0-14)
    - **nitrogen_kg_per_acre**: Nitrogen content
    - **phosphorus_kg_per_acre**: Phosphorus content
    - **potassium_kg_per_acre**: Potassium content
    - **organic_carbon_percent**: Organic carbon percentage
    - **notes**: Additional notes

    Validates: AC3 - System provides soil-based fertilizer recommendations
    """
    try:
        # Verify plot ownership
        verify_plot_ownership(test_data.plot_id, current_user.id, db)

        # Create soil test
        db_test = SoilTest(
            plot_id=test_data.plot_id,
            test_date=test_data.test_date,
            ph_level=test_data.ph_level,
            nitrogen_kg_per_acre=test_data.nitrogen_kg_per_acre,
            phosphorus_kg_per_acre=test_data.phosphorus_kg_per_acre,
            potassium_kg_per_acre=test_data.potassium_kg_per_acre,
            organic_carbon_percent=test_data.organic_carbon_percent,
            notes=test_data.notes,
        )

        db.add(db_test)
        db.commit()
        db.refresh(db_test)

        logger.info(f"Soil test created for plot {test_data.plot_id}")

        return SoilTestResponse.from_orm(db_test)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Create soil test error: {e}")
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/tests/plot/{plot_id}", response_model=List[SoilTestResponse])
async def get_plot_soil_tests(
    plot_id: int,
    current_user: CurrentFarmer,
    db: DB,
    limit: int = Query(10, ge=1, le=100, description="Maximum number of records"),
):
    """
    Get soil test history for a plot

    Returns recent soil tests ordered by date (newest first).
    """
    try:
        # Verify plot ownership
        verify_plot_ownership(plot_id, current_user.id, db)

        # Get tests
        tests = (
            db.query(SoilTest)
            .filter(SoilTest.plot_id == plot_id)
            .order_by(SoilTest.test_date.desc())
            .limit(limit)
            .all()
        )

        return [SoilTestResponse.from_orm(test) for test in tests]

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get soil tests error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve soil tests",
        )


@router.put("/tests/{test_id}", response_model=SoilTestResponse)
async def update_soil_test(
    test_id: int, test_update: SoilTestUpdate, current_user: CurrentFarmer, db: DB
):
    """Update soil test record"""
    try:
        # Get test
        test = db.query(SoilTest).filter(SoilTest.id == test_id).first()

        if not test:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Soil test not found")

        # Verify ownership
        verify_plot_ownership(test.plot_id, current_user.id, db)

        # Update fields
        update_data = test_update.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(test, field, value)

        db.commit()
        db.refresh(test)

        logger.info(f"Soil test {test_id} updated")

        return SoilTestResponse.from_orm(test)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Update soil test error: {e}")
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


# Fertilizer Application Endpoints


@router.post(
    "/fertilizer", response_model=FertilizerApplicationResponse, status_code=status.HTTP_201_CREATED
)
async def record_fertilizer_application(
    application_data: FertilizerApplicationCreate, current_user: CurrentFarmer, db: DB
):
    """
    Record fertilizer application

    - **plot_id**: Plot ID
    - **application_date**: Date of application
    - **fertilizer_type**: Type (organic, urea, dap, mop, npk, mixed)
    - **quantity_kg**: Quantity in kg
    - **cost_inr**: Cost in INR
    - **notes**: Additional notes
    """
    try:
        # Verify plot ownership
        verify_plot_ownership(application_data.plot_id, current_user.id, db)

        # Create application record
        db_application = FertilizerApplication(
            plot_id=application_data.plot_id,
            application_date=application_data.application_date,
            fertilizer_type=application_data.fertilizer_type,
            quantity_kg=application_data.quantity_kg,
            cost_inr=application_data.cost_inr,
            notes=application_data.notes,
        )

        db.add(db_application)
        db.commit()
        db.refresh(db_application)

        logger.info(f"Fertilizer application recorded for plot {application_data.plot_id}")

        return FertilizerApplicationResponse.from_orm(db_application)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Record fertilizer application error: {e}")
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/fertilizer/plot/{plot_id}", response_model=List[FertilizerApplicationResponse])
async def get_plot_fertilizer_applications(
    plot_id: int,
    current_user: CurrentFarmer,
    db: DB,
    limit: int = Query(20, ge=1, le=100, description="Maximum number of records"),
):
    """
    Get fertilizer application history for a plot

    Returns recent applications ordered by date (newest first).
    """
    try:
        # Verify plot ownership
        verify_plot_ownership(plot_id, current_user.id, db)

        # Get applications
        applications = (
            db.query(FertilizerApplication)
            .filter(FertilizerApplication.plot_id == plot_id)
            .order_by(FertilizerApplication.application_date.desc())
            .limit(limit)
            .all()
        )

        return [FertilizerApplicationResponse.from_orm(app) for app in applications]

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get fertilizer applications error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve fertilizer applications",
        )


# Soil Amendment Endpoints


@router.post(
    "/amendments", response_model=SoilAmendmentResponse, status_code=status.HTTP_201_CREATED
)
async def record_soil_amendment(
    amendment_data: SoilAmendmentCreate, current_user: CurrentFarmer, db: DB
):
    """
    Record soil amendment application

    - **plot_id**: Plot ID
    - **amendment_date**: Date of amendment
    - **amendment_type**: Type (lime, gypsum, sulfur, compost, biochar)
    - **quantity_kg**: Quantity in kg
    - **purpose**: Purpose of amendment
    - **cost_inr**: Cost in INR
    """
    try:
        # Verify plot ownership
        verify_plot_ownership(amendment_data.plot_id, current_user.id, db)

        # Create amendment record
        db_amendment = SoilAmendment(
            plot_id=amendment_data.plot_id,
            amendment_date=amendment_data.amendment_date,
            amendment_type=amendment_data.amendment_type,
            quantity_kg=amendment_data.quantity_kg,
            purpose=amendment_data.purpose,
            cost_inr=amendment_data.cost_inr,
        )

        db.add(db_amendment)
        db.commit()
        db.refresh(db_amendment)

        logger.info(f"Soil amendment recorded for plot {amendment_data.plot_id}")

        return SoilAmendmentResponse.from_orm(db_amendment)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Record soil amendment error: {e}")
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/amendments/plot/{plot_id}", response_model=List[SoilAmendmentResponse])
async def get_plot_soil_amendments(
    plot_id: int,
    current_user: CurrentFarmer,
    db: DB,
    limit: int = Query(20, ge=1, le=100, description="Maximum number of records"),
):
    """
    Get soil amendment history for a plot

    Returns recent amendments ordered by date (newest first).
    """
    try:
        # Verify plot ownership
        verify_plot_ownership(plot_id, current_user.id, db)

        # Get amendments
        amendments = (
            db.query(SoilAmendment)
            .filter(SoilAmendment.plot_id == plot_id)
            .order_by(SoilAmendment.amendment_date.desc())
            .limit(limit)
            .all()
        )

        return [SoilAmendmentResponse.from_orm(amend) for amend in amendments]

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get soil amendments error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve soil amendments",
        )


# Soil Health Summary


@router.get("/health/plot/{plot_id}", response_model=SoilHealthSummary)
async def get_plot_soil_health_summary(plot_id: int, current_user: CurrentFarmer, db: DB):
    """
    Get comprehensive soil health summary for a plot

    Returns latest soil test, recent fertilizer applications, amendments,
    and calculated soil health metrics.
    """
    try:
        # Verify plot ownership
        plot = verify_plot_ownership(plot_id, current_user.id, db)

        # Get latest soil test
        latest_test = (
            db.query(SoilTest)
            .filter(SoilTest.plot_id == plot_id)
            .order_by(SoilTest.test_date.desc())
            .first()
        )

        # Get recent fertilizer applications (last 12 months)
        one_year_ago = datetime.now().date() - timedelta(days=365)
        recent_fertilizers = (
            db.query(FertilizerApplication)
            .filter(
                and_(
                    FertilizerApplication.plot_id == plot_id,
                    FertilizerApplication.application_date >= one_year_ago,
                )
            )
            .order_by(FertilizerApplication.application_date.desc())
            .limit(10)
            .all()
        )

        # Get recent amendments (last 12 months)
        recent_amendments = (
            db.query(SoilAmendment)
            .filter(
                and_(SoilAmendment.plot_id == plot_id, SoilAmendment.amendment_date >= one_year_ago)
            )
            .order_by(SoilAmendment.amendment_date.desc())
            .limit(10)
            .all()
        )

        # Calculate total fertilizer cost (last year)
        total_cost = (
            db.query(func.sum(FertilizerApplication.cost_inr))
            .filter(
                and_(
                    FertilizerApplication.plot_id == plot_id,
                    FertilizerApplication.application_date >= one_year_ago,
                    FertilizerApplication.cost_inr.isnot(None),
                )
            )
            .scalar()
            or 0.0
        )

        # Calculate soil health score (simple algorithm)
        soil_health_score = None
        if latest_test:
            score = 0.0
            factors = 0

            # pH score (optimal 6.0-7.5)
            if latest_test.ph_level:
                if 6.0 <= latest_test.ph_level <= 7.5:
                    score += 100
                elif 5.5 <= latest_test.ph_level <= 8.0:
                    score += 70
                else:
                    score += 40
                factors += 1

            # Organic carbon score (optimal > 0.5%)
            if latest_test.organic_carbon_percent:
                if latest_test.organic_carbon_percent >= 0.75:
                    score += 100
                elif latest_test.organic_carbon_percent >= 0.5:
                    score += 70
                else:
                    score += 40
                factors += 1

            # NPK availability (simplified)
            if latest_test.nitrogen_kg_per_acre and latest_test.nitrogen_kg_per_acre >= 200:
                score += 80
                factors += 1
            if latest_test.phosphorus_kg_per_acre and latest_test.phosphorus_kg_per_acre >= 20:
                score += 80
                factors += 1
            if latest_test.potassium_kg_per_acre and latest_test.potassium_kg_per_acre >= 200:
                score += 80
                factors += 1

            if factors > 0:
                soil_health_score = round(score / factors, 1)

        return SoilHealthSummary(
            plot_id=plot_id,
            plot_name=plot.name,
            latest_test=SoilTestResponse.from_orm(latest_test) if latest_test else None,
            recent_fertilizer_applications=[
                FertilizerApplicationResponse.from_orm(app) for app in recent_fertilizers
            ],
            recent_amendments=[
                SoilAmendmentResponse.from_orm(amend) for amend in recent_amendments
            ],
            total_fertilizer_cost_last_year=float(total_cost),
            soil_health_score=soil_health_score,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get soil health summary error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve soil health summary",
        )
