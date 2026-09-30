"""
Livestock Breeding API Endpoints
Handles breeding optimization, cycle tracking, offspring management, and reports
"""

from datetime import date
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from app.core.auth import get_current_active_user
from app.schemas.breeding import (
    BreedingProgramReportRequest,
    BreedingProgramReportResponse,
    BreedingRecommendationRequest,
    BreedingRecommendationResponse,
    BreedingRecordCreate,
    BreedingRecordResponse,
    BreedingRecordUpdate,
    OffspringCreate,
    OffspringResponse,
    OffspringUpdate,
)
from app.services.livestock_breeding_service import get_breeding_service

router = APIRouter(
    prefix="/livestock-breeding",
    tags=["livestock-breeding"],
    dependencies=[Depends(get_current_active_user)],
)
# ============================================================================
# Breeding Record Endpoints
# ============================================================================


@router.get("")
async def breeding_root_alias(farmer_id: Optional[int] = Query(None)):
    """Registry alias for breeding list"""
    return await list_breeding_records(farmer_id=farmer_id)


@router.post("/records", response_model=BreedingRecordResponse, status_code=201)
async def create_breeding_record(record: BreedingRecordCreate):
    """
    Create a new breeding record

    - **livestock_id**: Parent livestock ID
    - **breeding_type**: natural or artificial_insemination
    - **breeding_date**: Date of breeding
    - **mate_id**: Mate livestock ID (optional)
    - **mate_breed**: Mate breed if external (optional)
    """
    try:
        service = get_breeding_service()
        result = service.create_breeding_record(record.model_dump())
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating breeding record: {str(e)}")


@router.get("/records/{record_id}", response_model=BreedingRecordResponse)
async def get_breeding_record(record_id: int):
    """Get breeding record by ID"""
    try:
        service = get_breeding_service()
        result = service.get_breeding_record(record_id)
        if not result:
            raise HTTPException(status_code=404, detail="Breeding record not found")
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching breeding record: {str(e)}")


@router.put("/records/{record_id}", response_model=BreedingRecordResponse)
async def update_breeding_record(record_id: int, record: BreedingRecordUpdate):
    """
    Update breeding record

    Use this endpoint to update pregnancy status, delivery dates, and other details
    """
    try:
        service = get_breeding_service()
        result = service.update_breeding_record(record_id, record.model_dump(exclude_unset=True))
        if not result:
            raise HTTPException(status_code=404, detail="Breeding record not found")
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating breeding record: {str(e)}")


@router.delete("/records/{record_id}", status_code=204)
async def delete_breeding_record(record_id: int):
    """Delete breeding record (soft delete)"""
    try:
        service = get_breeding_service()
        success = service.delete_breeding_record(record_id)
        if not success:
            raise HTTPException(status_code=404, detail="Breeding record not found")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting breeding record: {str(e)}")


@router.get("/records", response_model=List[BreedingRecordResponse])
async def list_breeding_records(
    livestock_id: Optional[int] = Query(None, description="Filter by livestock ID"),
    farmer_id: Optional[int] = Query(None, description="Filter by farmer ID"),
    pregnancy_status: Optional[str] = Query(None, description="Filter by pregnancy status"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
):
    """
    List breeding records with optional filters

    - **livestock_id**: Filter by specific livestock
    - **farmer_id**: Filter by farmer
    - **pregnancy_status**: Filter by status (pending, confirmed, delivered, failed)
    """
    try:
        service = get_breeding_service()
        results = service.list_breeding_records(
            livestock_id=livestock_id,
            farmer_id=farmer_id,
            pregnancy_status=pregnancy_status,
            skip=skip,
            limit=limit,
        )
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error listing breeding records: {str(e)}")


# ============================================================================
# Offspring Endpoints
# ============================================================================


@router.post("/offspring", response_model=OffspringResponse, status_code=201)
async def create_offspring(offspring: OffspringCreate):
    """
    Create offspring record

    - **breeding_record_id**: Parent breeding record ID
    - **birth_date**: Date of birth
    - **gender**: male or female (optional)
    - **birth_weight**: Birth weight in kg (optional)
    """
    try:
        service = get_breeding_service()
        result = service.create_offspring(offspring.model_dump())
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating offspring: {str(e)}")


@router.get("/offspring/{offspring_id}", response_model=OffspringResponse)
async def get_offspring(offspring_id: int):
    """Get offspring by ID"""
    try:
        service = get_breeding_service()
        result = service.get_offspring(offspring_id)
        if not result:
            raise HTTPException(status_code=404, detail="Offspring not found")
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching offspring: {str(e)}")


@router.put("/offspring/{offspring_id}", response_model=OffspringResponse)
async def update_offspring(offspring_id: int, offspring: OffspringUpdate):
    """
    Update offspring record

    Use this endpoint to track growth, weight updates, weaning, and sales
    """
    try:
        service = get_breeding_service()
        result = service.update_offspring(offspring_id, offspring.model_dump(exclude_unset=True))
        if not result:
            raise HTTPException(status_code=404, detail="Offspring not found")
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating offspring: {str(e)}")


@router.get("/offspring", response_model=List[OffspringResponse])
async def list_offspring(
    breeding_record_id: Optional[int] = Query(None, description="Filter by breeding record ID"),
    farmer_id: Optional[int] = Query(None, description="Filter by farmer ID"),
    health_status: Optional[str] = Query(None, description="Filter by health status"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
):
    """
    List offspring with optional filters

    - **breeding_record_id**: Filter by specific breeding record
    - **farmer_id**: Filter by farmer
    - **health_status**: Filter by status (healthy, weak, deceased)
    """
    try:
        service = get_breeding_service()
        results = service.list_offspring(
            breeding_record_id=breeding_record_id,
            farmer_id=farmer_id,
            health_status=health_status,
            skip=skip,
            limit=limit,
        )
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error listing offspring: {str(e)}")


# ============================================================================
# Breeding Recommendations Endpoint
# ============================================================================


@router.post("/recommendations", response_model=BreedingRecommendationResponse)
async def get_breeding_recommendations(request: BreedingRecommendationRequest):
    """
    Get AI-powered breeding recommendations for livestock

    Returns:
    - Recommended mate breeds with compatibility scores
    - Expected offspring traits
    - Optimal breeding season
    - Breeding tips and best practices

    This endpoint uses Amazon Bedrock AI to analyze genetics and performance history
    """
    try:
        service = get_breeding_service()
        result = service.get_breeding_recommendations(request.livestock_id)
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error generating breeding recommendations: {str(e)}"
        )


# ============================================================================
# Breeding Program Report Endpoint
# ============================================================================


@router.post("/program-report", response_model=BreedingProgramReportResponse)
async def generate_breeding_program_report(request: BreedingProgramReportRequest):
    """
    Generate comprehensive breeding program report

    Returns:
    - Breeding metrics (success rate, ROI, offspring count)
    - Offspring performance summary
    - Genetic improvement trends
    - Recommendations for program optimization

    Default period: Last 12 months if dates not specified
    """
    try:
        service = get_breeding_service()
        result = service.generate_breeding_program_report(
            farmer_id=request.farmer_id, start_date=request.start_date, end_date=request.end_date
        )
        return result
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error generating breeding program report: {str(e)}"
        )
