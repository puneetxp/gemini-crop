"""
Uploaded-file storage.

Cloud Run's filesystem is wiped on every restart, so in production files go to the GCS bucket
(settings.GCS_BUCKET). Locally, in tests, or if GCS is unreachable they go to UPLOAD_DIR.
Files are always served back through GET /api/v1/upload/files/{name}, so the bucket can stay private.
"""

import logging
import mimetypes
import os
import re
from typing import Optional, Tuple

from app.core.config import settings

logger = logging.getLogger(__name__)

UPLOAD_DIR = os.getenv("UPLOAD_DIR", "/tmp/uploads/quality_photos")
GCS_PREFIX = "uploads/"
_SAFE_NAME = re.compile(r"^[A-Za-z0-9._-]+$")


def _use_gcs() -> bool:
    mode = os.getenv("UPLOAD_STORAGE", "").lower()
    if mode in ("local", "gcs"):
        return mode == "gcs"
    # Default: GCS on Cloud Run, local disk everywhere else.
    return bool(os.getenv("K_SERVICE")) and bool(settings.GCS_BUCKET) and not settings.E2E_ACTIVE


def safe_name(filename: str) -> str:
    if not _SAFE_NAME.match(filename or "") or filename.startswith("."):
        raise ValueError("Invalid file name")
    return filename


def _bucket():
    from google.cloud import storage

    return storage.Client().bucket(settings.GCS_BUCKET)


def save(filename: str, content: bytes) -> str:
    """Store the file and return where it went ("gcs" or "local")."""
    filename = safe_name(filename)
    content_type = mimetypes.guess_type(filename)[0] or "application/octet-stream"
    if _use_gcs():
        try:
            _bucket().blob(GCS_PREFIX + filename).upload_from_string(
                content, content_type=content_type
            )
            return "gcs"
        except Exception as e:
            logger.error(
                f"GCS upload failed, keeping {filename} on local disk (lost on restart): {e}"
            )
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    with open(os.path.join(UPLOAD_DIR, filename), "wb") as f:
        f.write(content)
    return "local"


def load(filename: str) -> Optional[Tuple[bytes, str]]:
    """Return (content, content_type), or None if the file doesn't exist."""
    filename = safe_name(filename)
    content_type = mimetypes.guess_type(filename)[0] or "application/octet-stream"
    if _use_gcs():
        try:
            blob = _bucket().blob(GCS_PREFIX + filename)
            if blob.exists():
                return blob.download_as_bytes(), content_type
        except Exception as e:
            logger.error(f"GCS read failed for {filename}: {e}")
    path = os.path.join(UPLOAD_DIR, filename)
    if os.path.exists(path):
        with open(path, "rb") as f:
            return f.read(), content_type
    return None


def delete(filename: str) -> bool:
    filename = safe_name(filename)
    deleted = False
    if _use_gcs():
        try:
            blob = _bucket().blob(GCS_PREFIX + filename)
            if blob.exists():
                blob.delete()
                deleted = True
        except Exception as e:
            logger.error(f"GCS delete failed for {filename}: {e}")
    path = os.path.join(UPLOAD_DIR, filename)
    if os.path.exists(path):
        os.remove(path)
        deleted = True
    return deleted
