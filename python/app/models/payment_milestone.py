from __future__ import annotations
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from datetime import datetime as _datetime


class PaymentMilestone(BaseModel):
    id: int
    created_at: datetime
    updated_at: datetime
    enable: int
    milestone_type: str
    amount: float
    due_date: datetime
    paid_date: datetime | None = None
    status: str
    payment_method: str | None = None
    transaction_id: str | None = None
    booking_id: int


class PaymentMilestoneInput(BaseModel):
    enable: int | None = None
    milestone_type: str | None = None
    amount: float | None = None
    due_date: _datetime | None = None
    paid_date: _datetime | None = None
    status: str | None = None
    payment_method: str | None = None
    transaction_id: str | None = None
    booking_id: int | None = None
