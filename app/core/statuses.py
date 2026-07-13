from __future__ import annotations

from enum import StrEnum


class InvoiceStatus(StrEnum):
    DRAFT = "draft"
    ISSUED = "issued"
    CANCELLED = "cancelled"
    PAID = "paid"


class ExpenseStatus(StrEnum):
    DRAFT = "draft"
    APPROVED = "approved"
    REJECTED = "rejected"
    PAID = "paid"

