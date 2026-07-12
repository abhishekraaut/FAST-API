from __future__ import annotations

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.statuses import InvoiceStatus
from app.database.base import Base


class Invoice(Base):
    __tablename__ = "invoices"

    id: Mapped[int] = mapped_column(primary_key=True)
    organization_id: Mapped[int] = mapped_column(ForeignKey("organizations.id"), nullable=False, index=True)
    invoice_number: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    customer_name: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(String(50), default=InvoiceStatus.DRAFT.value, nullable=False)
    due_date: Mapped[str | None] = mapped_column(String(50), nullable=True)
    subtotal: Mapped[str] = mapped_column(String(50), default="0.00", nullable=False)
    tax_amount: Mapped[str] = mapped_column(String(50), default="0.00", nullable=False)
    total: Mapped[str] = mapped_column(String(50), default="0.00", nullable=False)
