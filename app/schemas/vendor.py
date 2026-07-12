from __future__ import annotations

from pydantic import BaseModel, ConfigDict, EmailStr


class VendorCreate(BaseModel):
    name: str
    email: EmailStr | None = None
    phone: str | None = None
    tax_number: str | None = None
    organization_id: int


class VendorOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    organization_id: int
    name: str
    email: str | None = None
    phone: str | None = None
    tax_number: str | None = None
    is_active: bool
