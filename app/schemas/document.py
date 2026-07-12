from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class DocumentCreate(BaseModel):
    document_type: str
    description: str | None = None


class DocumentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    organization_id: int
    document_type: str
    filename: str
    content_type: str
    storage_path: str | None = None
    status: str
    description: str | None = None
    error_message: str | None = None
