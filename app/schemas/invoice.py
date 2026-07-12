from __future__ import annotations

from decimal import Decimal

from pydantic import BaseModel, ConfigDict


class InvoiceItemCreate(BaseModel):
    description: str
    quantity: int = 1
    unit_price: str


class InvoiceCreate(BaseModel):
    customer_name: str
    due_date: str | None = None
    items: list[InvoiceItemCreate]


class InvoiceItemOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    description: str
    quantity: int
    unit_price: str
    line_total: str


class InvoiceOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    organization_id: int
    invoice_number: str
    customer_name: str
    status: str
    due_date: str | None = None
    subtotal: str
    tax_amount: str
    total: str
