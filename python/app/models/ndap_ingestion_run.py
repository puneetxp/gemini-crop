from __future__ import annotations
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from datetime import datetime as _datetime


class NdapIngestionRun(BaseModel):
    id: int
    created_at: datetime
    updated_at: datetime
    enable: int
    file_name: str
    file_hash: str
    started_at: datetime
    completed_at: datetime | None = None
    status: str
    records_ingested: int | None = None
    error_message: str | None = None


class NdapIngestionRunInput(BaseModel):
    enable: int | None = None
    file_name: str | None = None
    file_hash: str | None = None
    started_at: _datetime | None = None
    completed_at: _datetime | None = None
    status: str | None = None
    records_ingested: int | None = None
    error_message: str | None = None
