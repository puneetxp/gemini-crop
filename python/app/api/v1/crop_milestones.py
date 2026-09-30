"""
Crop Milestone Tracking API Endpoints

Validates: Requirements AC10 (Phase 6 - Required)
"""

from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import get_current_active_user, get_current_admin
from app.core.database import get_db
from app.services.crop_growth_tracker import get_crop_growth_tracker as get_crop_milestone_service

router = APIRouter(
    prefix="/crop-milestones",
    tags=["crop-milestones"],
    dependencies=[Depends(get_current_active_user)],
)


# Request/Response Models
class MilestoneCreate(BaseModel):
    """Request model for creating milestones"""

    crop_id: int = Field(..., description="Crop ID")
    crop_name: str = Field(..., description="Name of the crop")
    planting_date: datetime = Field(..., description="Date crop was planted")
    expected_harvest_date: datetime = Field(..., description="Expected harvest date")


class MilestoneUpdate(BaseModel):
    """Request model for updating milestone progress"""

    progress_percentage: int = Field(..., ge=0, le=100, description="Progress percentage (0-100)")
    actual_start_date: Optional[datetime] = Field(None, description="Actual start date")
    actual_end_date: Optional[datetime] = Field(None, description="Actual end date")
    notes: Optional[str] = Field(None, description="Farmer notes")


class StageTransitionAlert(BaseModel):
    """Request model for sending stage transition alert"""

    crop_id: int = Field(..., description="Crop ID")
    farmer_phone: str = Field(..., description="Farmer's phone number")
    farmer_email: Optional[str] = Field(None, description="Farmer's email")
    farmer_name: str = Field(..., description="Farmer's name")
    crop_name: str = Field(..., description="Name of the crop")
    new_stage: str = Field(..., description="New growth stage")


class MilestoneResponse(BaseModel):
    """Response model for milestone data"""

    crop_id: int
    stage: str
    expected_start_date: datetime
    expected_end_date: datetime
    actual_start_date: Optional[datetime]
    actual_end_date: Optional[datetime]
    status: str
    progress_percentage: int
    recommendations: str
    alert_sent: bool


class ProgressDashboardResponse(BaseModel):
    """Response model for progress dashboard"""

    crop_id: int
    crop_name: str
    crop_variety: Optional[str]
    planting_date: str
    expected_harvest_date: str
    days_to_harvest: int
    overall_progress: float
    current_stage: Optional[str]
    milestones: List[dict]
    status_summary: dict


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_milestones(
    request: MilestoneCreate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    """
    Create milestone tracking records for a newly planted crop

    Validates: AC10.1 - Track growth stages automatically
    """
    try:
        service = get_crop_milestone_service(db)
        milestones = await service.create_milestones_for_crop(
            crop_id=request.crop_id,
            crop_name=request.crop_name,
            planting_date=request.planting_date,
            expected_harvest_date=request.expected_harvest_date,
            user=current_user,
        )

        return {
            "success": True,
            "message": f"Created {len(milestones)} milestones for crop {request.crop_id}",
            "milestones": milestones,
        }

    except LookupError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating milestones: {str(e)}",
        )


@router.put("/{id}", status_code=status.HTTP_200_OK)
async def update_milestone_progress(
    id: int,
    request: MilestoneUpdate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    """
    Update milestone progress and status

    Validates: AC10.1 - Track growth stages automatically
    """
    try:
        service = get_crop_milestone_service(db)
        updated = await service.update_milestone_progress(
            milestone_id=id,
            progress_percentage=request.progress_percentage,
            actual_start_date=request.actual_start_date,
            actual_end_date=request.actual_end_date,
            notes=request.notes,
            user=current_user,
        )

        return {
            "success": True,
            "message": f"Milestone {id} updated successfully",
            "milestone": updated,
        }

    except LookupError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating milestone: {str(e)}",
        )


@router.post("/{id}/complete", status_code=status.HTTP_200_OK)
async def complete_milestone_alias(
    id: int, db: AsyncSession = Depends(get_db), current_user=Depends(get_current_active_user)
):
    """Registry alias for complete milestone"""
    return await update_milestone_progress(
        id, MilestoneUpdate(progress_percentage=100), db, current_user
    )


@router.get("/{crop_id}/current-stage", status_code=status.HTTP_200_OK)
async def get_current_stage(
    crop_id: int, db: AsyncSession = Depends(get_db), current_user=Depends(get_current_active_user)
):
    """
    Get current growth stage for a crop

    Validates: AC10.1 - Track growth stages automatically
    """
    try:
        service = get_crop_milestone_service(db)
        current_stage = await service.get_current_stage(crop_id, user=current_user)

        if not current_stage:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No active growth stage found for crop {crop_id}",
            )

        return {"success": True, "current_stage": current_stage}

    except HTTPException:
        raise
    except LookupError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting current stage: {str(e)}",
        )


@router.get("/{crop_id}/recommendations", status_code=status.HTTP_200_OK)
async def get_milestone_recommendations(
    crop_id: int,
    stage: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    """
    Get recommendations for current or specific growth stage

    Validates: AC10.2 - Provide milestone-based recommendations
    """
    try:
        service = get_crop_milestone_service(db)
        recommendations = await service.get_milestone_recommendations(
            crop_id=crop_id, stage=stage, user=current_user
        )

        if "error" in recommendations:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail=recommendations["error"]
            )

        return {"success": True, "recommendations": recommendations}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting recommendations: {str(e)}",
        )


@router.post("/send-stage-alert", status_code=status.HTTP_200_OK)
async def send_stage_transition_alert(
    request: StageTransitionAlert,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    """
    Send alert when crop transitions to new growth stage

    Validates: AC10.2 - Generate growth stage alerts via SNS
    """
    try:
        service = get_crop_milestone_service(db)

        # Get recommendations for the new stage
        recommendations_data = await service.get_milestone_recommendations(
            crop_id=request.crop_id, stage=request.new_stage, user=current_user
        )

        if "error" in recommendations_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail=recommendations_data["error"]
            )

        # Send alert
        result = await service.send_stage_transition_alert(
            crop_id=request.crop_id,
            farmer_phone=request.farmer_phone,
            farmer_email=request.farmer_email,
            farmer_name=request.farmer_name,
            crop_name=request.crop_name,
            new_stage=request.new_stage,
            recommendations=recommendations_data["recommendations"],
        )

        return {
            "success": result.get("success", False),
            "message": (
                "Stage transition alert sent successfully"
                if result.get("success")
                else "Failed to send alert"
            ),
            "notification": result,
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error sending stage alert: {str(e)}",
        )


@router.get("/{id}", response_model=ProgressDashboardResponse, status_code=status.HTTP_200_OK)
async def get_progress_dashboard(
    id: int, db: AsyncSession = Depends(get_db), current_user=Depends(get_current_active_user)
):
    """
    Get progress tracking dashboard data for a crop

    Validates: AC10.3 - Progress tracking dashboard with visual timeline
    """
    try:
        service = get_crop_milestone_service(db)
        dashboard = await service.get_progress_dashboard(id, user=current_user)

        if "error" in dashboard:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=dashboard["error"])

        return dashboard

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting progress dashboard: {str(e)}",
        )


@router.post(
    "/update-stages", status_code=status.HTTP_200_OK, dependencies=[Depends(get_current_admin)]
)
async def check_and_update_stages(
    db: AsyncSession = Depends(get_db), current_user=Depends(get_current_active_user)
):
    """
    Background job endpoint to check and update crop growth stages

    Validates: AC10.1 - Track growth stages automatically
    """
    try:
        service = get_crop_milestone_service(db)
        result = await service.check_and_update_stages()

        return {"success": True, "message": "Stage update job completed", "result": result}

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error in stage update job: {str(e)}",
        )
