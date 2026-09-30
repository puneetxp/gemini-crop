"""
Firestore service for managing real-time notifications, session caching, and state.
"""

import datetime
import logging
from typing import Any, Dict, List, Optional

from google.cloud import firestore

from app.core.config import settings

logger = logging.getLogger(__name__)


class FirestoreService:
    """Service to handle real-time state, caching, and notifications using Google Cloud Firestore"""

    def __init__(self):
        self._db = None
        self._init_client()

    def _init_client(self):
        try:
            # Firestore will auto-authenticate using environment credentials
            self._db = firestore.Client(project=settings.GOOGLE_CLOUD_PROJECT)
            logger.info("Firestore client initialized successfully")
        except Exception as e:
            logger.warning(f"Firestore initialization failed: {e}. Running in fallback/mock mode.")
            self._db = None

    def get_collection(self, collection_name: str):
        if not self._db:
            return None
        prefix = settings.FIRESTORE_COLLECTION_PREFIX
        return self._db.collection(f"{prefix}_{collection_name}" if prefix else collection_name)

    def set_document(self, collection: str, doc_id: str, data: Dict[str, Any]):
        if not self._db:
            return
        try:
            self.get_collection(collection).document(str(doc_id)).set(data)
        except Exception as e:
            logger.error(f"Firestore set_document error in collection '{collection}': {e}")

    def get_document(self, collection: str, doc_id: str) -> Optional[Dict[str, Any]]:
        if not self._db:
            return None
        try:
            doc = self.get_collection(collection).document(str(doc_id)).get()
            return doc.to_dict() if doc.exists else None
        except Exception as e:
            logger.error(f"Firestore get_document error in collection '{collection}': {e}")
            return None

    def add_notification(self, user_id: int, notification_type: str, message: str) -> bool:
        """Adds a notification to user's notifications collection"""
        data = {
            "user_id": user_id,
            "type": notification_type,
            "message": message,
            "created_at": datetime.datetime.utcnow().isoformat(),
            "read": False,
        }
        if not self._db:
            logger.info(f"Mock notification for user {user_id}: [{notification_type}] {message}")
            return True
        try:
            self.get_collection("notifications").add(data)
            logger.info(f"Notification added to Firestore for user {user_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to add notification to Firestore: {e}")
            return False


# Singleton instance
firestore_service = FirestoreService()
