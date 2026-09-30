"""
Satellite crop health per farm (Sentinel-2): NDVI / NDMI / NDRE trend, a
plain reading of it, and field images. See services/satellite_health.py.
"""

import logging
from typing import Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException, Query

from app.core.auth import get_current_active_user
from app.core.db import DB
from app.core.ownership import owner_condition
from app.services.satellite_health import farm_health

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/satellite", tags=["Satellite"], dependencies=[Depends(get_current_active_user)])

FARM_COLUMNS = "t.id, t.name, t.latitude, t.longitude, t.total_area, t.cultivable_area, t.area_unit, t.location_state, t.location_district"


def _my_farms(user_id: int, farm_id: int = None) -> List[Dict[str, Any]]:
    where = f"({owner_condition('farms', user_id)})"
    bind: List[Any] = []
    if farm_id is not None:
        where += " AND t.id = ?"
        bind.append(farm_id)
    return DB.raw(f"SELECT {FARM_COLUMNS} FROM farms t WHERE {where} ORDER BY t.id LIMIT 10", bind).result or []


@router.get("/farm/{farm_id}", response_model=Dict[str, Any])
async def farm_satellite(farm_id: int, refresh: bool = Query(False), current_user=Depends(get_current_active_user)):
    """Crop health from Sentinel-2 for one of the farmer's farms."""
    farms = _my_farms(current_user.id, farm_id)
    if not farms:
        raise HTTPException(status_code=404, detail="Farm not found")
    return {"success": True, "data": {"farm_name": farms[0]["name"], **await farm_health(farms[0], refresh=refresh)}}


@router.get("/my-farms", response_model=Dict[str, Any])
async def my_farms_satellite(current_user=Depends(get_current_active_user)):
    """Latest reading for each of the farmer's farms (for the dashboard)."""
    out = []
    for farm in _my_farms(current_user.id)[:5]:
        health = await farm_health(farm)
        out.append({
            "farm_id": farm["id"],
            "farm_name": farm["name"],
            "summary": health.get("summary") or {"status": health.get("status")},
            "observations": health.get("observations", [])[:8],
            "images": health.get("images"),
        })
    return {"success": True, "data": out}
