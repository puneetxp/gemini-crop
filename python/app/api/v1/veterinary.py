"""
Veterinary Services API
Task 28.2: Build veterinary services integration

Endpoints:
- POST /veterinary/symptom-check - Check symptoms and get triage
- POST /veterinary/remote-diagnosis - Get comprehensive remote diagnosis
- POST /veterinary/save-diagnosis - Save diagnosis as health record
- Doctor directory: /veterinary/doctors - add/find/connect with a livestock doctor
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field

from app.core.auth import get_current_active_user
from app.schemas.veterinarian import VeterinarianCreate, VeterinarianResponse, VeterinarianUpdate
from app.services.veterinarian_directory_service import veterinarian_directory_service
from app.services.veterinary_service import veterinary_service

# The doctor directory is public (farmers can look up a vet before signing in); everything else needs sign-in.
router = APIRouter(prefix="/veterinary", tags=["veterinary"])
signed_in = [Depends(get_current_active_user)]


class SymptomCheckRequest(BaseModel):
    """Request model for symptom check"""

    livestock_id: int = Field(..., description="Livestock ID")
    symptoms: List[str] = Field(..., description="List of observed symptoms")
    duration_days: int = Field(..., ge=0, description="How long symptoms have been present")
    additional_info: Optional[str] = Field(None, description="Additional observations")


class RemoteDiagnosisRequest(BaseModel):
    """Request model for remote diagnosis"""

    livestock_id: int = Field(..., description="Livestock ID")
    symptoms: List[str] = Field(..., description="List of observed symptoms")
    duration_days: int = Field(..., ge=0, description="Duration of symptoms in days")
    temperature_celsius: Optional[float] = Field(
        None, ge=35.0, le=45.0, description="Body temperature"
    )
    photos: Optional[List[str]] = Field(None, description="Photo URLs (future feature)")
    additional_info: Optional[str] = Field(None, description="Additional observations")


class SaveDiagnosisRequest(BaseModel):
    """Request model for saving diagnosis"""

    livestock_id: int = Field(..., description="Livestock ID")
    diagnosis: Dict[str, Any] = Field(..., description="Diagnosis results")
    veterinarian_name: Optional[str] = Field(None, description="Veterinarian name if consulted")


@router.get("/appointments", response_model=Dict[str, Any], dependencies=signed_in)
async def get_appointments_alias():
    """Registry alias for veterinary appointments"""
    return {
        "success": True,
        "message": "Veterinary appointments system operational",
        "appointments": [],
    }


@router.post("/symptom-check", status_code=status.HTTP_200_OK, dependencies=signed_in)
async def check_symptoms(request: SymptomCheckRequest):
    """
    Check symptoms against disease database and perform AI triage

    Returns symptom analysis with:
    - Possible diseases matched from database
    - AI-powered diagnosis from Bedrock
    - Triage assessment (low/medium/high severity)
    - Recommended actions and timeframe
    """
    try:
        result = veterinary_service.check_symptoms(
            livestock_id=request.livestock_id,
            symptoms=request.symptoms,
            duration_days=request.duration_days,
            additional_info=request.additional_info,
        )

        return {
            "success": True,
            "data": result,
            "message": f"Symptom check completed. Severity: {result['triage']['severity']}",
        }

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error checking symptoms: {str(e)}",
        )


@router.post("/remote-diagnosis", status_code=status.HTTP_200_OK, dependencies=signed_in)
async def get_remote_diagnosis(request: RemoteDiagnosisRequest):
    """
    Get comprehensive remote diagnosis with treatment recommendations

    Returns complete diagnosis including:
    - Symptom analysis and triage
    - AI-powered diagnosis with confidence level
    - Detailed treatment plan with medications
    - Follow-up schedule
    - Cost estimates
    - Telemedicine options (placeholder for partnerships)
    """
    try:
        result = veterinary_service.get_remote_diagnosis(
            livestock_id=request.livestock_id,
            symptoms=request.symptoms,
            duration_days=request.duration_days,
            temperature_celsius=request.temperature_celsius,
            photos=request.photos,
            additional_info=request.additional_info,
        )

        return {
            "success": True,
            "data": result,
            "message": "Remote diagnosis completed successfully",
        }

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting remote diagnosis: {str(e)}",
        )


@router.post("/save-diagnosis", status_code=status.HTTP_201_CREATED, dependencies=signed_in)
async def save_diagnosis(request: SaveDiagnosisRequest):
    """
    Save diagnosis results as health record

    Creates a health record entry with:
    - Diagnosis details
    - Treatment plan
    - Veterinarian information (if consulted)
    """
    try:
        result = veterinary_service.save_diagnosis_record(
            livestock_id=request.livestock_id,
            diagnosis=request.diagnosis,
            veterinarian_name=request.veterinarian_name,
        )

        return {"success": True, "data": result, "message": "Diagnosis saved successfully"}

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error saving diagnosis: {str(e)}",
        )


@router.get("/diseases/{species}", status_code=status.HTTP_200_OK)
async def get_disease_database(species: str):
    """
    Get disease database for a specific species

    Returns list of common diseases with:
    - Disease name
    - Common symptoms
    - Severity level
    - Contagious status
    - Treatment information
    """
    try:
        species_lower = species.lower()
        diseases = veterinary_service.DISEASE_DATABASE.get(species_lower, [])

        if not diseases:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No disease database found for species: {species}",
            )

        return {
            "success": True,
            "data": {"species": species, "diseases": diseases, "total_diseases": len(diseases)},
            "message": f"Disease database retrieved for {species}",
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving disease database: {str(e)}",
        )


# ---------------------------------------------------------------------------
# Doctor directory: add a livestock doctor and connect with them by
# phone / WhatsApp / email.
# ---------------------------------------------------------------------------


def _ensure_can_edit(doctor_id: int, current_user) -> None:
    doctor = veterinarian_directory_service.find(doctor_id)
    if not doctor:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Doctor not found")
    if (
        doctor.get("added_by_user_id") != current_user.id
        and getattr(current_user, "user_type", None) != "admin"
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the person who added this doctor can change it",
        )


@router.post("/doctors", response_model=Dict[str, Any], status_code=status.HTTP_201_CREATED)
async def add_doctor(request: VeterinarianCreate, current_user=Depends(get_current_active_user)):
    """Add a veterinarian to the directory so farmers can find and contact them"""
    try:
        data = request.model_dump()
        data["added_by_user_id"] = current_user.id
        result = veterinarian_directory_service.create(data)
        return {
            "success": True,
            "data": VeterinarianResponse(**result),
            "message": "Doctor added successfully",
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error adding doctor: {str(e)}",
        )


@router.get("/doctors", response_model=Dict[str, Any])
async def list_doctors(
    species: Optional[str] = Query(
        None, description="Filter by species treated, e.g. cattle, goat, poultry"
    ),
    state: Optional[str] = Query(None, description="Filter by state served"),
    district: Optional[str] = Query(None, description="Filter by district served"),
    available_only: bool = Query(False, description="Only doctors currently available"),
    verified_only: bool = Query(False, description="Only verified doctors"),
):
    """Find livestock doctors, optionally filtered by species and location"""
    try:
        results = veterinarian_directory_service.search(
            species=species,
            state=state,
            district=district,
            available_only=available_only,
            verified_only=verified_only,
        )
        return {
            "success": True,
            "data": [VeterinarianResponse(**r) for r in results],
            "total": len(results),
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error listing doctors: {str(e)}",
        )


@router.get("/doctors/{doctor_id}", response_model=Dict[str, Any])
async def get_doctor(doctor_id: int):
    """Get a doctor's profile and ready-to-use call/WhatsApp/email links"""
    result = veterinarian_directory_service.find(doctor_id)
    if not result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Doctor not found")
    return {"success": True, "data": VeterinarianResponse(**result)}


@router.put("/doctors/{doctor_id}", response_model=Dict[str, Any])
async def update_doctor(
    doctor_id: int, request: VeterinarianUpdate, current_user=Depends(get_current_active_user)
):
    """Update a doctor's directory entry (whoever added it, or an admin)"""
    _ensure_can_edit(doctor_id, current_user)
    result = veterinarian_directory_service.update(
        doctor_id, request.model_dump(exclude_unset=True)
    )
    if not result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Doctor not found")
    return {
        "success": True,
        "data": VeterinarianResponse(**result),
        "message": "Doctor updated successfully",
    }


@router.delete("/doctors/{doctor_id}", status_code=status.HTTP_200_OK)
async def remove_doctor(doctor_id: int, current_user=Depends(get_current_active_user)):
    """Remove a doctor from the directory (whoever added it, or an admin)"""
    _ensure_can_edit(doctor_id, current_user)
    deleted = veterinarian_directory_service.delete(doctor_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Doctor not found")
    return {"success": True, "message": "Doctor removed successfully"}
