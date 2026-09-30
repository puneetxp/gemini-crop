"""
Pest and Disease Early Warning API
Provides pest/disease risk monitoring and management recommendations

Validates: Requirements AC10 (Phase 6 - Required)
Task 25.2: Build pest and disease early warning system
"""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import get_current_active_user
from app.core.database import get_db
from app.services.crop_milestone_service import get_service as get_crop_milestone_service
from app.services.farm_access import (
    clean,
    crop_for_user,
    farm_for_user,
    fetch_all,
    fetch_one,
    is_admin,
)
from app.services.pest_disease_service import get_pest_disease_service
from app.services.weather_service import get_weather_service

router = APIRouter(
    prefix="/pest-disease", tags=["pest-disease"], dependencies=[Depends(get_current_active_user)]
)


# Data access: raw SQL through app.core.db.DB (app/orm classes are not SQLAlchemy models).
# Owner scoping: crops / farms / alerts of other users are 404.
def _owned_crop(crop_id: int, user):
    try:
        return crop_for_user(crop_id, user)
    except LookupError:
        raise HTTPException(status_code=404, detail="Crop not found")


def _owned_farm(farm_id: int, user):
    try:
        return farm_for_user(farm_id, user)
    except LookupError:
        raise HTTPException(status_code=404, detail="Farm not found")


def _alert_dict(alert) -> dict:
    """Plain dict for an alert row (replaces the old ORM to_dict())."""
    return dict(clean(alert))


class WeatherConditions(BaseModel):
    """Weather conditions for risk assessment"""

    temperature: float = Field(..., description="Temperature in Celsius")
    humidity: int = Field(..., ge=0, le=100, description="Humidity percentage")
    rainfall: float = Field(default=0.0, ge=0, description="Rainfall in mm")


class RiskCheckRequest(BaseModel):
    """Request to check pest/disease risk"""

    crop_id: int = Field(..., description="Crop ID")
    weather_data: WeatherConditions
    current_stage: str = Field(..., description="Current growth stage")


class ManagementRecommendation(BaseModel):
    """Pest/disease management recommendation"""

    pest_disease: str
    timing: str
    prevention: List[str]
    organic_options: Optional[List[str]] = None
    chemical_options: Optional[List[str]] = None


class RiskAlert(BaseModel):
    """Pest/disease risk alert"""

    pest_disease: str
    severity: str
    description: str
    current_conditions: dict
    management: dict
    detected_at: str


@router.post("/identify", response_model=List[RiskAlert])
async def identify_risks_alias(
    request: RiskCheckRequest,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    """Registry alias for pest/disease identification"""
    return await check_pest_disease_risk(request, db, current_user)


@router.post("/check-risk", response_model=List[RiskAlert])
async def check_pest_disease_risk(
    request: RiskCheckRequest,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    """
    Check for pest and disease risks based on weather and crop stage

    Validates: AC10.3 - Early warning alerts based on weather and crop stage
    """
    _owned_crop(request.crop_id, current_user)
    try:
        service = get_pest_disease_service(db)

        risks = await service.check_pest_disease_risk(
            crop_id=request.crop_id,
            weather_data=request.weather_data.model_dump(),
            current_stage=request.current_stage,
            user=current_user,
        )

        return risks

    except LookupError:
        raise HTTPException(status_code=404, detail="Crop not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/treatments", response_model=List[dict])
async def get_treatments_alias(
    pest_disease: str = Query(..., description="Pest or disease name"),
    preference: str = Query(default="both", pattern="^(organic|chemical|both)$"),
    db: AsyncSession = Depends(get_db),
):
    """Registry alias for treatments"""
    res = await get_management_recommendations(pest_disease, preference, db)
    return [res] if isinstance(res, dict) else res


@router.get("/management/{pest_disease}", response_model=ManagementRecommendation)
async def get_management_recommendations(
    pest_disease: str,
    preference: str = Query(default="both", pattern="^(organic|chemical|both)$"),
    db: AsyncSession = Depends(get_db),
):
    """
    Get pest/disease management recommendations

    Args:
        pest_disease: Name of pest or disease (e.g., 'aphids', 'fungal_diseases')
        preference: Treatment preference ('organic', 'chemical', or 'both')

    Validates: AC10.3 - Pest management recommendations with organic and chemical options
    """
    try:
        service = get_pest_disease_service(db)

        recommendations = await service.get_management_recommendations(
            pest_disease=pest_disease, preference=preference
        )

        if "error" in recommendations:
            raise HTTPException(status_code=404, detail=recommendations["error"])

        return recommendations

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/crop-risks/{crop_id}")
async def get_crop_specific_risks(
    crop_id: int,
    current_stage: str = Query(..., description="Current growth stage"),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    """
    Get common pest/disease risks for specific crop and stage

    Validates: AC10.3 - Crop-specific pest/disease information
    """
    try:
        service = get_pest_disease_service(db)

        # Get crop details to determine crop name (owner-scoped)
        crop = _owned_crop(crop_id, current_user)

        if not crop:
            raise HTTPException(status_code=404, detail="Crop not found")

        risks = await service.get_crop_specific_risks(
            crop_name=crop.crop_name, current_stage=current_stage
        )

        return {
            "crop_id": crop_id,
            "crop_name": crop.crop_name,
            "current_stage": current_stage,
            "risks": risks,
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/prevention-guidance/{crop_id}")
async def get_prevention_guidance(
    crop_id: int,
    current_stage: str = Query(..., description="Current growth stage"),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    """
    Get disease prevention guidance for current crop stage

    Validates: AC10.3 - Disease prevention guidance with timing and application instructions
    """
    _owned_crop(crop_id, current_user)
    try:
        service = get_pest_disease_service(db)

        guidance = await service.get_prevention_guidance(
            crop_id=crop_id, current_stage=current_stage
        )

        return guidance

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/monitor-all")
async def monitor_all_crops(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    """
    Background job endpoint to monitor all active crops for pest/disease risks

    This endpoint should be called by a scheduled job (cron/celery)

    Validates: AC10.3 - Automated pest/disease monitoring
    """
    # Scans every farmer's crops, so only an admin (or the scheduler's admin account) may run it.
    if not is_admin(current_user):
        raise HTTPException(status_code=403, detail="Admin access required")
    try:
        service = get_pest_disease_service(db)
        weather_service = get_weather_service(db)
        milestone_service = get_crop_milestone_service()  # generated factory takes no args

        summary = await service.monitor_crops_for_risks(
            weather_service=weather_service, milestone_service=milestone_service
        )

        return summary

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/available-pests")
async def get_available_pests():
    """
    Get list of all pests and diseases tracked by the system

    Returns list of pest/disease names with descriptions
    """
    from app.services.pest_disease_service import PEST_DISEASE_THRESHOLDS

    pests = []
    for pest_disease, data in PEST_DISEASE_THRESHOLDS.items():
        pests.append(
            {
                "name": pest_disease,
                "description": data["description"],
                "severity": data["severity"],
                "risk_stages": data["risk_stages"],
            }
        )

    return {"total": len(pests), "pests_diseases": pests}


@router.get("/history/{crop_id}")
async def get_pest_disease_history(
    crop_id: int,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    """Get historical pest/disease records for a specific crop"""
    _owned_crop(crop_id, current_user)
    try:
        alerts = fetch_all(
            "SELECT * FROM pest_disease_alerts WHERE crop_id = ? ORDER BY created_at DESC, id DESC",
            [crop_id],
        )

        return {"crop_id": crop_id, "history": [_alert_dict(alert) for alert in alerts]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/alerts", response_model=List[dict])
async def get_all_alerts_alias(
    farm_id: Optional[int] = Query(None),
    crop_id: Optional[int] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    """Registry alias for alerts"""
    if crop_id:
        res = await get_crop_alerts(
            crop_id, include_resolved=False, db=db, current_user=current_user
        )
        return res.get("alerts", [])
    if farm_id:
        res = await get_farm_alerts(
            farm_id, include_resolved=False, limit=50, db=db, current_user=current_user
        )
        return res.get("alerts", [])
    return []


@router.get("/alerts/{crop_id}")
async def get_crop_alerts(
    crop_id: int,
    include_resolved: bool = Query(default=False, description="Include resolved alerts"),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    """
    Get all pest/disease alerts for a specific crop

    Args:
        crop_id: Crop ID
        include_resolved: Whether to include resolved alerts

    Returns:
        List of alerts for the crop
    """
    _owned_crop(crop_id, current_user)
    try:
        sql = "SELECT * FROM pest_disease_alerts WHERE crop_id = ?"
        if not include_resolved:
            sql += " AND COALESCE(is_resolved, 0) = 0"
        alerts = fetch_all(sql + " ORDER BY created_at DESC, id DESC", [crop_id])

        return {
            "crop_id": crop_id,
            "total_alerts": len(alerts),
            "alerts": [_alert_dict(alert) for alert in alerts],
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/alerts/{alert_id}/resolve")
async def resolve_alert(
    alert_id: int,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    """
    Mark a pest/disease alert as resolved

    Args:
        alert_id: Alert ID

    Returns:
        Updated alert
    """
    try:
        from datetime import datetime

        alert = fetch_one(
            """SELECT a.*, f.user_id AS farm_user_id FROM pest_disease_alerts a
               LEFT JOIN farms f ON f.id = a.farm_id WHERE a.id = ?""",
            [alert_id],
        )
        if not alert or (not is_admin(current_user) and alert.farm_user_id != current_user.id):
            raise HTTPException(status_code=404, detail="Alert not found")

        alert = fetch_one(
            """UPDATE pest_disease_alerts SET is_resolved = 1, resolved_at = ?, updated_at = CURRENT_TIMESTAMP
               WHERE id = ? RETURNING *""",
            [datetime.now(), alert_id],
        )

        return {"success": True, "message": "Alert marked as resolved", "alert": _alert_dict(alert)}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/alerts/farm/{farm_id}")
async def get_farm_alerts(
    farm_id: int,
    include_resolved: bool = Query(default=False, description="Include resolved alerts"),
    limit: int = Query(default=50, le=100, description="Maximum number of alerts"),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    """
    Get all pest/disease alerts for a specific farm

    Args:
        farm_id: Farm ID
        include_resolved: Whether to include resolved alerts
        limit: Maximum number of alerts to return

    Returns:
        List of alerts for the farm
    """
    _owned_farm(farm_id, current_user)
    try:
        sql = "SELECT * FROM pest_disease_alerts WHERE farm_id = ?"
        if not include_resolved:
            sql += " AND COALESCE(is_resolved, 0) = 0"
        alerts = fetch_all(
            sql + " ORDER BY created_at DESC, id DESC LIMIT ?", [farm_id, int(limit)]
        )

        return {
            "farm_id": farm_id,
            "total_alerts": len(alerts),
            "alerts": [_alert_dict(alert) for alert in alerts],
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
