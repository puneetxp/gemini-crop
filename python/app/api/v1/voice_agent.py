"""
Multilingual Voice Query Agent API Endpoint

Accepts audio recordings from farmers, uses Gemini's multimodal (audio) capability
to transcribe + answer agricultural questions in the farmer's own language
(Hindi, Tamil, Telugu, Kannada, Marathi, Bengali, English, etc.)

Demonstrates:
- Multimodal AI (audio understanding) — Google Cloud Hackathon criterion
- Accessibility and Inclusive Communities — Hackathon solution area
- Conversational Analytics / Natural Language Interfaces — Hackathon criterion
"""

import json
import logging
import re
from typing import Any, Dict, Optional

from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from app.core.config import settings

logger = logging.getLogger(__name__)
from fastapi import Depends

from app.core.auth import get_current_active_user

router = APIRouter(
    prefix="/voice", tags=["Voice AI"], dependencies=[Depends(get_current_active_user)]
)
SUPPORTED_AUDIO_TYPES = {
    "audio/wav",
    "audio/wave",
    "audio/x-wav",
    "audio/mpeg",
    "audio/mp3",
    "audio/ogg",
    "audio/webm",
    "audio/flac",
    "audio/aac",
    "audio/mp4",
}

VOICE_SYSTEM_PROMPT = """You are CropSense Voice Assistant — an expert agricultural advisor for Indian farmers.

A farmer has sent you a voice message. You must:
1. TRANSCRIBE the audio accurately (it may be in Hindi, Tamil, Telugu, Kannada, Marathi, Bengali, Punjabi, Gujarati, or English).
2. DETECT which language the farmer spoke in.
3. ANSWER their agricultural question in THE SAME LANGUAGE they used.
4. Keep answers practical, helpful, and under 200 words.

Return your response as JSON with EXACTLY this structure (no markdown, no extra text):
{
    "transcription": "The farmer's spoken words transcribed as text",
    "language_detected": "Hindi | Tamil | Telugu | Kannada | Marathi | Bengali | Punjabi | Gujarati | English",
    "response_text": "Your agricultural advice in the same language",
    "topic": "crop_advisory | pest_disease | weather | market_prices | livestock | soil | fertilizer | general"
}
"""


@router.post("/query", response_model=Dict[str, Any])
async def voice_query(
    audio: UploadFile = File(
        ..., description="Audio recording of the farmer's question (WAV/MP3/OGG/WebM)"
    ),
    farm_id: Optional[int] = Form(None, description="Optional farm ID for contextual answers"),
    current_user=Depends(get_current_active_user),
):
    """
    Send a voice recording and receive an AI-powered agricultural response
    in the farmer's own language.

    Supports: Hindi, Tamil, Telugu, Kannada, Marathi, Bengali, Punjabi, Gujarati, English.

    Uses **Gemini Multimodal (Audio)** to transcribe and answer in one shot.
    This demonstrates **Accessibility**, **Multimodal AI**, and **Conversational Analytics**.
    """
    # Validate content type
    content_type = audio.content_type or "audio/wav"
    if content_type not in SUPPORTED_AUDIO_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported audio format '{content_type}'. Accepted: WAV, MP3, OGG, WebM, FLAC, AAC.",
        )

    audio_bytes = await audio.read()

    if len(audio_bytes) > 25 * 1024 * 1024:  # 25MB limit
        raise HTTPException(status_code=413, detail="Audio file too large. Maximum 25MB.")

    if len(audio_bytes) < 500:
        raise HTTPException(status_code=400, detail="Audio file appears too small or corrupted.")

    logger.info(
        f"Voice query: format={content_type}, size={len(audio_bytes)} bytes, farm_id={farm_id}"
    )

    # Build context from farm if provided
    farm_context = ""
    if farm_id:
        try:
            from app.agents.agent_tools import get_farm_details, set_agent_user

            set_agent_user(current_user)  # farm context only for the signed-in user's own farm
            farm_context = f"\n\nFarmer's farm context:\n{get_farm_details(farm_id)}"
        except Exception as e:
            logger.debug(f"Could not load farm context: {e}")

    # Call Gemini multimodal with audio
    try:
        import vertexai
        from vertexai.generative_models import GenerationConfig, GenerativeModel, Part

        vertexai.init(project=settings.GOOGLE_CLOUD_PROJECT, location=settings.GEMINI_LOCATION)

        model = GenerativeModel(settings.GEMINI_MODEL)
        audio_part = Part.from_data(data=audio_bytes, mime_type=content_type)

        prompt = VOICE_SYSTEM_PROMPT
        if farm_context:
            prompt += farm_context

        generation_config = GenerationConfig(
            max_output_tokens=1000,
            temperature=0.3,
        )

        response = model.generate_content([audio_part, prompt], generation_config=generation_config)

        text = response.text.strip()

        # Parse JSON response
        json_match = re.search(r"\{.*\}", text, re.DOTALL)
        if json_match:
            result = json.loads(json_match.group())
        else:
            result = {
                "transcription": text,
                "language_detected": "Unknown",
                "response_text": text,
                "topic": "general",
            }

        result["model_used"] = settings.GEMINI_MODEL
        result["multimodal"] = "audio"

        # Log to BigQuery
        _log_voice_event(result)

        return {"success": True, "data": result}

    except Exception as e:
        logger.error(f"Voice query processing failed: {e}")

        # Graceful fallback with mock response
        return {
            "success": True,
            "data": {
                "transcription": "(Audio processing unavailable — Gemini multimodal not configured)",
                "language_detected": "English",
                "response_text": "Voice processing is currently running in fallback mode. Please use text chat.",
                "topic": "general",
                "model_used": "mock-fallback",
                "multimodal": "audio",
            },
        }


def _log_voice_event(result: Dict[str, Any]):
    """Stream voice query event to BigQuery."""
    try:
        from app.services.bigquery_service import bigquery_service

        bigquery_service.log_event(
            "voice_queries",
            {
                "language": result.get("language_detected", "Unknown"),
                "topic": result.get("topic", "general"),
                "model_used": result.get("model_used", ""),
            },
        )
    except Exception as e:
        logger.debug(f"BigQuery voice logging skipped: {e}")


# ---------------------------------------------------------------------------
# Assistant: voice or text -> open a menu option, answer, or propose a record
# ---------------------------------------------------------------------------

import base64
from datetime import date
from typing import List

from pydantic import BaseModel, Field

import time

from app.services.voice_assist_audit import record_attempt
from app.services.voice_assist_service import (
    build_prompt,
    keyword_fallback,
    parse_model_json,
    sanitize_result,
)


class MenuEntry(BaseModel):
    id: str = Field(..., max_length=64)
    label: str = Field(..., max_length=300)


class AnimalEntry(BaseModel):
    id: int
    label: str = Field(..., max_length=200)


class ChatTurn(BaseModel):
    role: str = Field(..., pattern="^(user|assistant)$")
    text: str = Field(..., max_length=1000)


class AssistRequest(BaseModel):
    # Either a recording (base64) or typed text
    audio_base64: Optional[str] = None
    mime_type: Optional[str] = "audio/webm"
    # Recording length as measured by the browser (for the voice log)
    duration_ms: Optional[int] = Field(None, ge=0, le=600000)
    text: Optional[str] = Field(None, max_length=1000)
    query: Optional[str] = Field(None, max_length=1000)
    lang: str = "en"
    menu: List[MenuEntry] = Field(default_factory=list, max_length=200)
    # The farmer's own livestock, so the assistant can ask "which animal?"
    animals: List[AnimalEntry] = Field(default_factory=list, max_length=200)
    history: List[ChatTurn] = Field(default_factory=list, max_length=20)
    focus_animal_id: Optional[int] = None
    # Guided form filling ("add_livestock"): the draft so far, updated each turn
    task: Optional[str] = Field(None, pattern="^(add_livestock)$")
    draft: Dict[str, Any] = Field(default_factory=dict)
    # The farmer's own farms and crops, so proposals can target them ("which farm?")
    farms: List[AnimalEntry] = Field(default_factory=list, max_length=100)
    crops: List[AnimalEntry] = Field(default_factory=list, max_length=200)
    # Plain-text summary of the farmer's own farms, crops, livestock and dashboard figures
    context: Optional[str] = Field(None, max_length=12000)


@router.post("/assist", response_model=Dict[str, Any])
async def voice_assist(request: AssistRequest, current_user=Depends(get_current_active_user)):
    """
    Understand a voice recording or typed text and decide what to do:
    open a menu option, answer briefly, or propose a record for the user to
    approve. Nothing is written to the database here.
    """
    effective_text = (request.text or request.query or "").strip()
    if not request.audio_base64 and not effective_text:
        raise HTTPException(status_code=400, detail="Send a voice recording or some text.")
    request.text = effective_text

    menu = [m.model_dump() for m in request.menu]
    menu_ids = [m["id"] for m in menu]

    audio_bytes = b""
    mime = (request.mime_type or "audio/webm").split(";")[0].strip()
    if request.audio_base64:
        if mime not in SUPPORTED_AUDIO_TYPES:
            raise HTTPException(status_code=400, detail=f"Unsupported audio format '{mime}'.")
        try:
            audio_bytes = base64.b64decode(request.audio_base64, validate=True)
        except Exception:
            raise HTTPException(status_code=400, detail="Audio is not valid base64.")
        if len(audio_bytes) > 10 * 1024 * 1024:
            raise HTTPException(status_code=413, detail="Recording too long. Maximum 10MB.")
        if len(audio_bytes) < 500:
            raise HTTPException(status_code=400, detail="Recording is too short.")

    started = time.monotonic()
    # What goes in the voice log for this call (filled in as we go)
    audit: Dict[str, Any] = {
        "source": "voice" if audio_bytes else "text",
        "task": request.task,
        "ui_lang": request.lang,
        "mime_type": mime if audio_bytes else None,
        "audio_bytes": len(audio_bytes) or None,
        "duration_ms": request.duration_ms,
    }
    model_errors: List[str] = []

    animals = [a.model_dump() for a in request.animals]
    prompt = build_prompt(
        menu,
        request.lang,
        date.today().isoformat(),
        request.text,
        animals=animals,
        history=[h.model_dump() for h in request.history],
        focus_animal_id=request.focus_animal_id,
        task=request.task,
        draft=request.draft,
        context=request.context,
        farms=[f.model_dump() for f in request.farms],
        crops=[c.model_dump() for c in request.crops],
    )

    try:
        # google-genai client (the vertexai.generative_models SDK is deprecated)
        from google import genai
        from google.genai import types

        client = genai.Client(
            vertexai=True,
            project=settings.GOOGLE_CLOUD_PROJECT,
            location=settings.GEMINI_LOCATION,
        )
        contents: List[Any] = [prompt]
        if audio_bytes:
            contents.insert(0, types.Part.from_bytes(data=audio_bytes, mime_type=mime))

        config = types.GenerateContentConfig(
            # Room for a data table when answering from the farmer's data
            max_output_tokens=2000 if request.context else 1000,
            temperature=0.2,
            response_mime_type="application/json",
        )
        # Flash-Lite first (fast, cheap); if it's unavailable in this project/region, use the main model
        models = list(dict.fromkeys([settings.GEMINI_ASSIST_MODEL, settings.GEMINI_MODEL, settings.GEMINI_FALLBACK_MODEL]))
        response, model_used = None, models[0]
        for model_used in models:
            try:
                response = await client.aio.models.generate_content(
                    model=model_used, contents=contents, config=config
                )
                break
            except Exception as model_error:
                logger.warning(f"Assist model {model_used} failed: {model_error}")
                model_errors.append(f"{model_used}: {model_error}")
        if response is None:
            raise RuntimeError("No assistant model available — " + " | ".join(model_errors))
        result = sanitize_result(
            parse_model_json(response.text),
            menu_ids,
            request.lang,
            [a["id"] for a in animals],
            task=request.task,
            draft=request.draft,
            farm_ids=[f.id for f in request.farms],
            crop_ids=[c.id for c in request.crops],
        )
        result["model_used"] = model_used
        record_attempt(
            current_user.id,
            **audit,
            language_detected=result["language"],
            transcript=result["transcript"] or request.text,
            intent=result["intent"],
            model_used=model_used,
            # A model before this one failed: keep why, even though the call succeeded
            error=" | ".join(model_errors) or None,
            latency_ms=int((time.monotonic() - started) * 1000),
        )
        _log_voice_event(
            {"language_detected": result["language"], "topic": result["intent"], "model_used": model_used}
        )
        return {"success": True, "data": result}

    except Exception as e:
        logger.error(f"Voice assist failed: {e}")
        record_attempt(
            current_user.id,
            **audit,
            transcript=request.text,
            status="error" if audio_bytes and not request.text else "fallback",
            error=str(e),
            latency_ms=int((time.monotonic() - started) * 1000),
        )
        if audio_bytes and not request.text:
            # Can't understand audio without the model — ask the client to fall back to typing/search
            raise HTTPException(
                status_code=503,
                detail="Voice understanding is unavailable right now. Please type or pick from the menu.",
            )
        return {"success": True, "data": keyword_fallback(request.text or "", menu, request.lang)}
