from datetime import datetime
from pydantic import BaseModel, Field


class FileModel(BaseModel):

    name: str = Field(examples=['Photo'])
    extension: str = Field(examples=['.jpg'])
    size: int = Field(examples=[1024])
    path: str = Field(examples=['storage/pics'])
    created_at: datetime
    updated_at: datetime | None
    comment: str | None = Field(examples=['My first photo.'])
