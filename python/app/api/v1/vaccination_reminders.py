"""
Vaccination Reminder API Endpoints

Provides REST API for vaccination reminder management, compliance tracking,
and automated notification scheduling.

Task 27.3: Build vaccination reminder system
Validates: Requirements AC12 (Phase 7 - Required)
"""

import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from app.services.vaccination_reminder_service import get_vaccination_reminder_service

logger = logging.getLogger(__name__)

from fastapi import Depends

from app.core.auth import get_current_active_user

router = APIRouter(
    prefix="/vaccination-reminders",
    tags=["vaccination-reminders"],
    dependencies=[Depends(get_current_active_user)],
)
# ==================== REQUEST/RESPONSE MODELS ====================


class ReminderRequest(BaseModel):
    """Request model for sending vaccination reminders"""

    farmer_id: int = Field(..., description="Farmer's user ID")
    farmer_phone: str = Field(..., description="Farmer's phone number (E.164 format)")
    days_ahead: int = Field(
        7, description="Days to look ahead for upcoming vaccinations", ge=1, le=30
    )


class ComplianceRequest(BaseModel):
    """Request model for compliance calculations"""

    livestock_id: Optional[int] = Field(None, description="Specific livestock ID (optional)")
    farmer_id: Optional[int] = Field(None, description="Farmer ID for overall compliance")


# ==================== ENDPOINTS ====================


@router.get("", response_model=Dict[str, Any])
async def get_vaccination_reminders_root():
    """Registry alias for vaccination reminders root"""
    return {
        "status": "success",
        "message": "Vaccination reminder system operational",
        "features": ["upcoming", "compliance", "dashboard"],
    }


@router.get("/upcoming/{farmer_id}")
async def get_upcoming_vaccinations(
    farmer_id: int, days_ahead: int = Query(7, description="Days to look ahead", ge=1, le=30)
):
    """
    Get upcoming vaccinations for all farmer's livestock

    Args:
        farmer_id: Farmer's user ID
        days_ahead: Number of days to look ahead (default: 7)

    Returns:
        List of upcoming vaccinations requiring attention
    """
    try:
        service = get_vaccination_reminder_service()
        upcoming = service.check_upcoming_vaccinations(farmer_id, days_ahead)

        return {
            "farmer_id": farmer_id,
            "days_ahead": days_ahead,
            "total_upcoming": len(upcoming),
            "vaccinations": upcoming,
        }

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error getting upcoming vaccinations: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve upcoming vaccinations")


@router.post("/send-reminders")
async def send_vaccination_reminders(request: ReminderRequest):
    """
    Send vaccination reminders for all upcoming vaccinations

    Args:
        request: Reminder request with farmer details

    Returns:
        Summary of reminders sent
    """
    try:
        service = get_vaccination_reminder_service()
        result = service.send_batch_reminders(
            farmer_id=request.farmer_id,
            farmer_phone=request.farmer_phone,
            days_ahead=request.days_ahead,
        )

        return {
            "success": True,
            "message": f"Sent {result['sent']} vaccination reminders",
            "details": result,
        }

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error sending vaccination reminders: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to send vaccination reminders")


@router.get("/compliance/livestock/{livestock_id}")
async def get_livestock_compliance(livestock_id: int):
    """
    Get vaccination compliance rate for specific livestock

    Args:
        livestock_id: Livestock ID

    Returns:
        Compliance metrics for the livestock
    """
    try:
        service = get_vaccination_reminder_service()
        compliance = service.calculate_compliance_rate(livestock_id)

        return {"success": True, "compliance": compliance}

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error calculating livestock compliance: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to calculate compliance rate")


@router.get("/compliance/farmer/{farmer_id}")
async def get_farmer_compliance(farmer_id: int):
    """
    Get overall vaccination compliance for all farmer's livestock

    Args:
        farmer_id: Farmer's user ID

    Returns:
        Farmer-level compliance metrics
    """
    try:
        service = get_vaccination_reminder_service()
        compliance = service.calculate_farmer_compliance(farmer_id)

        return {"success": True, "compliance": compliance}

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error calculating farmer compliance: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to calculate compliance rate")


@router.get("/report/{farmer_id}")
async def get_compliance_report(farmer_id: int):
    """
    Generate comprehensive vaccination compliance report

    Args:
        farmer_id: Farmer's user ID

    Returns:
        Detailed compliance report with recommendations
    """
    try:
        service = get_vaccination_reminder_service()
        report = service.generate_compliance_report(farmer_id)

        return {"success": True, "report": report}

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error generating compliance report: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to generate compliance report")


@router.get("/dashboard/{farmer_id}")
async def get_vaccination_dashboard(farmer_id: int):
    """
    Get vaccination dashboard metrics for farmer

    Combines compliance data and upcoming vaccinations for dashboard display

    Args:
        farmer_id: Farmer's user ID

    Returns:
        Dashboard metrics including compliance and upcoming vaccinations
    """
    try:
        service = get_vaccination_reminder_service()

        # Get compliance data
        compliance = service.calculate_farmer_compliance(farmer_id)

        # Get upcoming vaccinations
        upcoming = service.check_upcoming_vaccinations(farmer_id, days_ahead=30)

        # Categorize by urgency
        overdue = [v for v in upcoming if v.get("overdue", False)]
        urgent = [v for v in upcoming if not v.get("overdue") and v["days_until_due"] <= 7]
        soon = [v for v in upcoming if 7 < v["days_until_due"] <= 14]

        return {
            "success": True,
            "dashboard": {
                "compliance": {
                    "overall_rate": compliance["overall_compliance_rate"],
                    "status": compliance["compliance_status"],
                    "total_livestock": compliance["total_livestock"],
                    "completed": compliance["total_completed_vaccinations"],
                    "expected": compliance["total_expected_vaccinations"],
                },
                "upcoming": {
                    "overdue_count": len(overdue),
                    "urgent_count": len(urgent),
                    "soon_count": len(soon),
                    "total_count": len(upcoming),
                    "overdue": overdue[:5],  # Show top 5 overdue
                    "urgent": urgent[:5],  # Show top 5 urgent
                },
                "livestock_summary": compliance["livestock_compliance"],
            },
        }

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error getting vaccination dashboard: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve dashboard data")
