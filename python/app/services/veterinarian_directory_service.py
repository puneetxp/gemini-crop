"""
Veterinarian Directory Service
Manages the list of livestock doctors farmers can find and connect with,
and builds the tap-to-call / WhatsApp / email links used to reach them.
"""

import json
import logging
import re
from typing import Any, Dict, List, Optional

from app.orm.veterinarian import Veterinarian

logger = logging.getLogger(__name__)


class VeterinarianDirectoryService:
    """Service for managing the veterinarian directory"""

    def __init__(self):
        self.model = Veterinarian

    def _with_connect_links(self, record: Dict[str, Any]) -> Dict[str, Any]:
        """Attach tel:/wa.me/mailto: links and decode species_supported"""
        record = dict(record)

        species = record.get("species_supported")
        if isinstance(species, str) and species:
            try:
                record["species_supported"] = json.loads(species)
            except json.JSONDecodeError:
                record["species_supported"] = [species]
        elif not species:
            record["species_supported"] = []

        phone = record.get("phone")
        record["call_link"] = f"tel:{phone}" if phone else None

        whatsapp_number = record.get("whatsapp") or phone
        if whatsapp_number:
            digits = re.sub(r"[^\d+]", "", whatsapp_number)
            record["whatsapp_link"] = f"https://wa.me/{digits.lstrip('+')}"
        else:
            record["whatsapp_link"] = None

        email = record.get("email")
        record["email_link"] = f"mailto:{email}" if email else None

        return record

    # available_now/verified are SMALLINT columns; psycopg sends a Python bool
    # as a Postgres boolean, which Postgres won't implicitly cast to smallint.
    _BOOL_COLUMNS = ("available_now", "verified")

    def _coerce_booleans(self, data: Dict[str, Any]) -> Dict[str, Any]:
        data = dict(data)
        for col in self._BOOL_COLUMNS:
            if col in data and isinstance(data[col], bool):
                data[col] = 1 if data[col] else 0
        return data

    def create(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Add a veterinarian to the directory"""
        record_data = self._coerce_booleans(data)
        if "species_supported" in record_data and record_data["species_supported"] is not None:
            record_data["species_supported"] = json.dumps(record_data["species_supported"])

        result = self.model.create(record_data).get_inserted()
        logger.info(f"Added veterinarian {result['id']} to directory")
        return self._with_connect_links(result.to_dict())

    def find(self, veterinarian_id: int) -> Optional[Dict[str, Any]]:
        """Get a veterinarian by ID"""
        record = self.model.find(veterinarian_id)
        if not record:
            return None
        return self._with_connect_links(record.to_dict())

    def update(self, veterinarian_id: int, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update a veterinarian entry"""
        record = self.model.find(veterinarian_id)
        if not record:
            return None

        update_data = self._coerce_booleans({k: v for k, v in data.items() if v is not None})
        if "species_supported" in update_data:
            update_data["species_supported"] = json.dumps(update_data["species_supported"])

        record.update(update_data)
        updated = self.model.find(veterinarian_id)
        return self._with_connect_links(updated.to_dict())

    def delete(self, veterinarian_id: int) -> bool:
        """Remove a veterinarian from the directory"""
        record = self.model.find(veterinarian_id)
        if not record:
            return False
        rows_deleted = self.model.delete({"id": veterinarian_id})
        return rows_deleted > 0

    def search(
        self,
        species: Optional[str] = None,
        state: Optional[str] = None,
        district: Optional[str] = None,
        available_only: bool = False,
        verified_only: bool = False,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        """Search the directory, filtering on species/location in Python since
        species_supported is stored as a JSON text column."""
        where: Dict[str, Any] = {"enable": 1}
        if state:
            where["location_state"] = state
        if district:
            where["location_district"] = district
        if available_only:
            where["available_now"] = 1
        if verified_only:
            where["verified"] = 1

        results = self.model.where(where).get()
        records = results.to_dict() if results else []
        if isinstance(records, dict):
            records = [records]

        if species:
            species_lower = species.lower()
            records = [
                r
                for r in records
                if not r.get("species_supported")
                or species_lower in (r["species_supported"] or "").lower()
            ]

        records.sort(key=lambda r: (r.get("rating") or 0, r.get("verified") or 0), reverse=True)

        return [self._with_connect_links(r) for r in records[:limit]]


# Singleton instance
_veterinarian_directory_service_instance = None


def get_veterinarian_directory_service() -> VeterinarianDirectoryService:
    """Get singleton instance of veterinarian directory service"""
    global _veterinarian_directory_service_instance
    if _veterinarian_directory_service_instance is None:
        _veterinarian_directory_service_instance = VeterinarianDirectoryService()
    return _veterinarian_directory_service_instance


veterinarian_directory_service = get_veterinarian_directory_service()
