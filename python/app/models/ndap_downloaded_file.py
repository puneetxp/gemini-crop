from __future__ import annotations
from pydantic import BaseModel
from datetime import datetime
from datetime import datetime as _datetime


class NdapDownloadedFile(BaseModel):
    id: int
    created_at: datetime
    updated_at: datetime
    enable: int
    file_name: str
    file_hash: str
    file_content: str


class NdapDownloadedFileInput(BaseModel):
    enable: int | None = None
    file_name: str | None = None
    file_hash: str | None = None
    file_content: str | None = None
