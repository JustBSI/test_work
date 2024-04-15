from pydantic import BaseModel
from datetime import datetime


class FileCreate(BaseModel):
    name: str
    extension: str
    size: int
    path: str
    created_at: datetime
    updated_at: datetime | None = None
    comment: str | None = None
