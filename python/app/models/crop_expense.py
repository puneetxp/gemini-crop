from __future__ import annotations
from pydantic import BaseModel
from typing import Optional
from datetime import date, datetime
from datetime import date as _date, datetime as _datetime


class CropExpense(BaseModel):
    id: int
    created_at: datetime
    updated_at: datetime
    enable: int
    category: str
    amount: float
    description: str | None = None
    expense_date: date
    crop_id: int


class CropExpenseInput(BaseModel):
    enable: int | None = None
    category: str | None = None
    amount: float | None = None
    description: str | None = None
    expense_date: _date | None = None
    crop_id: int | None = None
