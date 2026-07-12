from __future__ import annotations

from decimal import Decimal

from pydantic import BaseModel, ConfigDict


class JournalEntryLineCreate(BaseModel):
    account_code: str
    debit: str | None = None
    credit: str | None = None


class JournalEntryCreate(BaseModel):
    description: str
    lines: list[JournalEntryLineCreate]


class JournalEntryLineOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    account_code: str
    debit: str
    credit: str


class JournalEntryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    organization_id: int
    description: str
    status: str
    lines: list[JournalEntryLineOut]
