"""
File Upload API endpoints
Handles photo uploads for quality verification and other features
"""

import logging
import os
import uuid
from datetime import datetime
from typing import Any, Dict

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from fastapi.responses import Response

from app.core.auth import get_current_active_user
from app.services import file_storage

logger = logging.getLogger(__name__)
router = APIRouter()

# Kept for backwards compatibility; storage location now lives in app/services/file_storage.py
UPLOAD_DIR = file_storage.UPLOAD_DIR

# Allowed file extensions
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp"}
DOCUMENT_EXTENSIONS = ALLOWED_EXTENSIONS | {".pdf"}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB

FILES_PATH = "/api/v1/upload/files"


async def _store(file: UploadFile, allowed: set) -> Dict[str, Any]:
    file_ext = os.path.splitext(file.filename or "")[1].lower()
    if file_ext not in allowed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid file type. Allowed types: {', '.join(sorted(allowed))}",
        )

    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File size exceeds maximum allowed size of {MAX_FILE_SIZE / (1024 * 1024)}MB",
        )

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{timestamp}_{uuid.uuid4().hex[:12]}{file_ext}"
    try:
        storage = file_storage.save(filename, content)
    except Exception as e:
        logger.error(f"Error uploading file: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to upload file"
        )

    logger.info(f"File uploaded ({storage}): {filename}")
    return {"success": True, "url": f"{FILES_PATH}/{filename}", "filename": filename}


@router.post("/image", response_model=Dict[str, Any])
async def upload_image(file: UploadFile = File(...), current_user=Depends(get_current_active_user)):
    """
    Upload an image for quality verification

    Returns the URL of the uploaded image
    """
    return await _store(file, ALLOWED_EXTENSIONS)


@router.post("/document", response_model=Dict[str, Any])
async def upload_document(
    file: UploadFile = File(...), current_user=Depends(get_current_active_user)
):
    """
    Upload a document (images or PDF)
    """
    return await _store(file, DOCUMENT_EXTENSIONS)


@router.get("/files/{filename}")
async def get_file(filename: str):
    """Serve an uploaded file. Names are random, so links work like unlisted URLs."""
    try:
        found = file_storage.load(filename)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid file name")
    if not found:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found")
    content, content_type = found
    return Response(
        content=content,
        media_type=content_type,
        headers={"Cache-Control": "private, max-age=86400"},
    )


@router.delete("/photo/{filename}", response_model=Dict[str, Any])
async def delete_photo(filename: str, current_user=Depends(get_current_active_user)):
    """
    Delete an uploaded photo
    """
    try:
        deleted = file_storage.delete(filename)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid file name")
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Photo not found")

    logger.info(f"Photo deleted successfully: {filename}")
    return {"success": True, "message": "Photo deleted successfully"}
