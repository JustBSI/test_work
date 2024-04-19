from pydantic import BaseModel, Field
from datetime import datetime


class FileCreate(BaseModel):

    name: str = Field(examples=['Photo'])
    extension: str = Field(examples=['.jpg'])
    size: int = Field(examples=[1024])
    path: str = Field(examples=['storage/pics'])
    created_at: datetime
    updated_at: datetime | None
    comment: str | None = Field(examples=['My first photo.'])
