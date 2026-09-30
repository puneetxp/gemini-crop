"""
Multimodal Vision Diagnosis API Endpoint

Accepts crop/plant image uploads and returns AI-powered disease diagnosis
using Gemini's multimodal (vision) capabilities.

Demonstrates: Multimodal AI for image understanding — Google Cloud Hackathon criterion.
"""

import logging
from typing import Any, Dict, Optional

from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from app.services.vision_diagnosis_service import vision_diagnosis_service

logger = logging.getLogger(__name__)
from fastapi import Depends

from app.core.auth import get_current_active_user

router = APIRouter(
    prefix="/vision", tags=["Vision AI"], dependencies=[Depends(get_current_active_user)]
)


@router.post("/diagnose", response_model=Dict[str, Any])
async def diagnose_crop_disease(
    image: UploadFile = File(..., description="Photo of the crop/leaf to diagnose"),
    crop_name: Optional[str] = Form(None, description="Name of the crop (e.g. Rice, Tomato)"),
    region: Optional[str] = Form(None, description="State or district for regional context"),
):
    """
    Upload a photo of a crop leaf/fruit and get an AI-powered disease diagnosis.

    Uses **Gemini Vision (multimodal)** to analyze the image and return:
    - Disease identification with confidence score
    - Severity assessment
    - Treatment options (organic, chemical, cultural)
    - Prevention recommendations
    - Urgency level

    This endpoint demonstrates **Multimodal AI** capabilities using Google Cloud Vertex AI.
    """
    # Validate file type
    allowed_types = {"image/jpeg", "image/png", "image/webp", "image/jpg"}
    if image.content_type not in allowed_types:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported image type '{image.content_type}'. Accepted: JPEG, PNG, WebP.",
        )

    # Read image bytes
    image_bytes = await image.read()

    if len(image_bytes) > 10 * 1024 * 1024:  # 10MB limit
        raise HTTPException(status_code=413, detail="Image too large. Maximum size is 10MB.")

    if len(image_bytes) < 1000:  # Suspiciously small
        raise HTTPException(status_code=400, detail="Image appears too small or corrupted.")

    logger.info(
        f"Vision diagnosis request: crop={crop_name}, region={region}, size={len(image_bytes)} bytes"
    )

    try:
        diagnosis = await vision_diagnosis_service.diagnose_from_bytes(
            image_bytes=image_bytes, mime_type=image.content_type, crop_name=crop_name, region=region
        )
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e)[:500])

    return {"success": True, "diagnosis": diagnosis}


@router.post("/diagnose-base64", response_model=Dict[str, Any])
async def diagnose_from_base64(payload: Dict[str, Any]):
    """
    Submit a base64-encoded crop image for AI disease diagnosis.

    Request body:
    ```json
    {
        "image_base64": "<base64 string>",
        "mime_type": "image/jpeg",
        "crop_name": "Rice",
        "region": "Maharashtra"
    }
    ```
    """
    image_b64 = payload.get("image_base64")
    if not image_b64:
        raise HTTPException(status_code=400, detail="Missing 'image_base64' field.")

    try:
        diagnosis = await vision_diagnosis_service.diagnose_from_base64(
            base64_image=image_b64,
            mime_type=payload.get("mime_type", "image/jpeg"),
            crop_name=payload.get("crop_name"),
            region=payload.get("region"),
            lang=payload.get("lang", "en"),
        )
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e)[:500])

    return {"success": True, "diagnosis": diagnosis}


# ---------------------------------------------------------------------------
# Diagnosis page: photo + the farmer's own crop -> diagnosis in their language,
# checked for banned pesticides and saved (district-level outbreak data)
# ---------------------------------------------------------------------------

import base64 as _b64
import json as _json

from pydantic import BaseModel, Field

from app.core.db import DB
from app.core.ownership import owner_condition

ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/jpg", "image/png", "image/webp"}
MAX_IMAGE_BYTES = 8 * 1024 * 1024


class CropDiagnoseRequest(BaseModel):
    image_base64: str
    mime_type: str = "image/jpeg"
    crop_id: Optional[int] = None
    crop_name: Optional[str] = Field(None, max_length=100)
    lang: str = Field("en", max_length=10)


def _crop_context(crop_id: int, user_id: int) -> Optional[Dict[str, Any]]:
    """The farmer's own crop with its farm's place (None if not theirs)."""
    rows = DB.raw(
        f"""SELECT t.crop_name, t.crop_variety, t.season, t.planting_date, f.id AS farm_id,
                   f.location_state, f.location_district, f.primary_soil_type, f.irrigation_type
            FROM crops t
            JOIN farm_plots p ON p.id = t.farm_plot_id
            JOIN farms f ON f.id = p.farm_id
            WHERE t.id = ? AND ({owner_condition('crops', user_id)})""",
        [crop_id],
    ).result
    return rows[0] if rows else None


@router.post("/diagnose-crop", response_model=Dict[str, Any])
async def diagnose_crop(request: CropDiagnoseRequest, current_user=Depends(get_current_active_user)):
    """Diagnose a crop photo for the signed-in farmer and keep the result."""
    mime = request.mime_type.split(";")[0].strip().lower()
    if mime not in ALLOWED_IMAGE_TYPES:
        raise HTTPException(status_code=400, detail="Please send a JPEG, PNG or WebP photo.")
    try:
        image = _b64.b64decode(request.image_base64, validate=True)
    except Exception:
        raise HTTPException(status_code=400, detail="The photo could not be read.")
    if len(image) > MAX_IMAGE_BYTES:
        raise HTTPException(status_code=413, detail="Photo too large. Maximum size is 8 MB.")
    if len(image) < 1000:
        raise HTTPException(status_code=400, detail="The photo is too small or damaged.")

    crop = _crop_context(request.crop_id, current_user.id) if request.crop_id else None
    if request.crop_id and not crop:
        raise HTTPException(status_code=404, detail="Crop not found")
    crop_name = request.crop_name or (crop or {}).get("crop_name")
    region = ", ".join(x for x in [(crop or {}).get("location_district"), (crop or {}).get("location_state")] if x) or None
    context = None
    if crop:
        bits = [
            f"variety {crop['crop_variety']}" if crop.get("crop_variety") else "",
            f"{crop['season']} season" if crop.get("season") else "",
            f"sown on {crop['planting_date']}" if crop.get("planting_date") else "",
            f"{crop['primary_soil_type']} soil" if crop.get("primary_soil_type") else "",
            f"{crop['irrigation_type']} irrigation" if crop.get("irrigation_type") else "",
        ]
        context = "Crop details: " + ", ".join(b for b in bits if b) + "." if any(bits) else None

    try:
        diagnosis = await vision_diagnosis_service.diagnose_from_bytes(
            image, mime, crop_name=crop_name, region=region, lang=request.lang, context=context
        )
    except RuntimeError as e:
        logger.error(f"Crop diagnosis failed: {e}")
        raise HTTPException(status_code=503, detail=str(e)[:500])

    saved_id = None
    if diagnosis.get("disease_detected") is not False or diagnosis.get("category"):
        try:
            conf = diagnosis.get("confidence")
            rows = DB.raw(
                """INSERT INTO crop_diagnoses (user_id, crop_id, farm_id, crop_name, state, district, disease_name,
                       scientific_name, category, severity, urgency, confidence, language, model_used, safety_flags, result)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?) RETURNING id""",
                [
                    current_user.id,
                    request.crop_id if crop else None,
                    (crop or {}).get("farm_id"),
                    (crop_name or diagnosis.get("crop_identified") or "")[:100] or None,
                    (crop or {}).get("location_state"),
                    (crop or {}).get("location_district"),
                    str(diagnosis.get("disease_name") or "")[:255] or None,
                    str(diagnosis.get("scientific_name") or "")[:255] or None,
                    str(diagnosis.get("category") or "")[:30] or None,
                    str(diagnosis.get("severity") or "")[:20] or None,
                    str(diagnosis.get("urgency") or "")[:20] or None,
                    round(min(max(float(conf), 0.0), 1.0), 3) if isinstance(conf, (int, float)) else None,
                    request.lang[:10],
                    diagnosis.get("model_used"),
                    len((diagnosis.get("safety") or {}).get("removed") or []),
                    _json.dumps(diagnosis, ensure_ascii=False),
                ],
            ).result
            saved_id = rows[0]["id"] if rows else None
        except Exception as e:
            logger.warning(f"crop_diagnoses insert failed: {e}")

    return {"success": True, "diagnosis": diagnosis, "id": saved_id}


@router.get("/diagnoses", response_model=Dict[str, Any])
async def my_diagnoses(limit: int = 20, current_user=Depends(get_current_active_user)):
    """The signed-in farmer's recent diagnoses, newest first."""
    rows = DB.raw(
        """SELECT id, created_at, crop_id, crop_name, disease_name, category, severity, urgency, confidence
           FROM crop_diagnoses WHERE user_id = ? ORDER BY created_at DESC, id DESC LIMIT ?""",
        [current_user.id, max(1, min(limit, 100))],
    ).result
    return {"success": True, "data": rows or []}
