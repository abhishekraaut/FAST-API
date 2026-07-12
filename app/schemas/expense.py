from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class ExpenseCreate(BaseModel):
    vendor_name: str
    amount: str
    description: str | None = None


class ExpenseOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    organization_id: int
    vendor_name: str
    description: str | None = None
    amount: str
    status: str
