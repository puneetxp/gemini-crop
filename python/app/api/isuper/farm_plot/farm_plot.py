from __future__ import annotations
from fastapi import APIRouter, HTTPException, Depends
from app.models.farm_plot import FarmPlot, FarmPlotInput
from app.services.farm_plot_service import get_service
from app.core.auth import get_current_admin
from typing import List, Dict


router = APIRouter(prefix="/isuper/farm_plot", tags=["isuper-farm_plot"],
                   dependencies=[Depends(get_current_admin)])
service = get_service()

@router.get("/", response_model=List[FarmPlot])
def list_isuper_farm_plot():
    return service.all()

@router.get("/{item_id}", response_model=FarmPlot)
def show_isuper_farm_plot(item_id: int):
    record = service.find(item_id)
    if not record:
        raise HTTPException(status_code=404, detail="Farm_plot not found")
    return record

@router.post("/", response_model=FarmPlot, status_code=201)
def create_isuper_farm_plot(payload: FarmPlotInput):
    return service.create(payload.dict(exclude_unset=True))

@router.put("/{item_id}", response_model=FarmPlot)
def update_isuper_farm_plot(item_id: int, payload: FarmPlotInput):
    updated = service.update(item_id, payload.dict(exclude_unset=True))
    if not updated:
        raise HTTPException(status_code=404, detail="Farm_plot not found")
    return updated

@router.delete("/{item_id}", response_model=Dict[str, bool])
def delete_isuper_farm_plot(item_id: int):
    if not service.delete(item_id):
        raise HTTPException(status_code=404, detail="Farm_plot not found")
    return {"success": True}
