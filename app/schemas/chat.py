from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class ChatSessionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    organization_id: int
    created_at: str


class ChatMessageCreate(BaseModel):
    content: str


class ChatMessageOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    session_id: int
    sender: str
    content: str
    intent: str | None = None
    created_at: str


class ChatQueryResponse(BaseModel):
    session_id: int
    response: str
    intent: str
    confidence: float
    entities: dict
