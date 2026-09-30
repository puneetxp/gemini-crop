from __future__ import annotations
from pydantic import BaseModel
from datetime import datetime
from datetime import datetime as _datetime


class ShcStateDistrictCode(BaseModel):
    id: int
    created_at: datetime
    updated_at: datetime
    enable: int
    state_name: str
    state_code: int
    district_name: str
    district_code: int


class ShcStateDistrictCodeInput(BaseModel):
    enable: int | None = None
    state_name: str | None = None
    state_code: int | None = None
    district_name: str | None = None
    district_code: int | None = None
