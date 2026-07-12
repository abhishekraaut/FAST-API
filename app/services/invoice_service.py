from __future__ import annotations

from decimal import Decimal
from random import randint

from sqlalchemy.orm import Session

from datetime import datetime, timezone

from app.core.statuses import InvoiceStatus
from app.models.account import Account
from app.models.invoice import Invoice
from app.models.invoice_item import InvoiceItem
from app.models.journal_entry import JournalEntry
from app.models.journal_entry_line import JournalEntryLine
from app.models.status_event import StatusEvent
from app.schemas.invoice import InvoiceCreate


class InvoiceService:
    def __init__(self, db: Session):
        self.db = db

    def create(self, payload: InvoiceCreate, organization_id: int) -> Invoice:
        invoice = Invoice(
            organization_id=organization_id,
            invoice_number=f"INV-{randint(1000, 9999)}",
            customer_name=payload.customer_name,
            due_date=payload.due_date,
            subtotal="0.00",
            tax_amount="0.00",
            total="0.00",
            status=InvoiceStatus.DRAFT.value,
        )
        self.db.add(invoice)
        self.db.flush()

        subtotal = Decimal("0.00")
        for item in payload.items:
            line_total = Decimal(str(item.unit_price)) * item.quantity
            subtotal += line_total
            self.db.add(
                InvoiceItem(
                    invoice_id=invoice.id,
                    description=item.description,
                    quantity=item.quantity,
                    unit_price=format(Decimal(str(item.unit_price)), ".2f"),
                    line_total=format(line_total, ".2f"),
                )
            )

        invoice.subtotal = format(subtotal, ".2f")
        invoice.total = format(subtotal, ".2f")
        self.db.add(invoice)
        self.db.commit()
        self.db.refresh(invoice)
        self._record_status_event(invoice, None, InvoiceStatus.DRAFT.value, "created")
        return invoice

    def _record_status_event(self, invoice: Invoice, from_status: str | None, to_status: str, reason: str) -> None:
        event = StatusEvent(
            organization_id=invoice.organization_id,
            entity_type="invoice",
            entity_id=invoice.id,
            from_status=from_status,
            to_status=to_status,
            reason=reason,
            created_at=datetime.now(timezone.utc).isoformat(),
        )
        self.db.add(event)
        self.db.commit()

    def list(self, organization_id: int) -> list[Invoice]:
        return self.db.query(Invoice).filter(Invoice.organization_id == organization_id).order_by(Invoice.id.desc()).all()

    def get(self, invoice_id: int, organization_id: int) -> Invoice:
        invoice = self.db.query(Invoice).filter(Invoice.id == invoice_id, Invoice.organization_id == organization_id).first()
        if not invoice:
            raise ValueError("Invoice not found")
        return invoice

    def cancel(self, invoice_id: int, organization_id: int) -> Invoice:
        invoice = self.db.query(Invoice).filter(Invoice.id == invoice_id, Invoice.organization_id == organization_id).first()
        if not invoice:
            raise ValueError("Invoice not found")

        invoice.status = InvoiceStatus.CANCELLED.value
        self.db.add(invoice)
        self.db.commit()
        self.db.refresh(invoice)
        self._record_status_event(invoice, InvoiceStatus.DRAFT.value, InvoiceStatus.CANCELLED.value, "cancelled")
        return invoice

    def issue(self, invoice_id: int, organization_id: int) -> Invoice:
        invoice = self.db.query(Invoice).filter(Invoice.id == invoice_id, Invoice.organization_id == organization_id).first()
        if not invoice:
            raise ValueError("Invoice not found")

        if invoice.status != "draft":
            return invoice

        receivable = self.db.query(Account).filter(Account.organization_id == organization_id, Account.code == "1100").first()
        revenue = self.db.query(Account).filter(Account.organization_id == organization_id, Account.code == "4000").first()
        if not receivable or not revenue:
            raise ValueError("Required accounts not found")

        journal = JournalEntry(
            organization_id=organization_id,
            description=f"Invoice issued {invoice.invoice_number}",
            status="posted",
        )
        self.db.add(journal)
        self.db.flush()

        total_amount = Decimal(str(invoice.total))
        self.db.add(
            JournalEntryLine(
                journal_entry_id=journal.id,
                account_code=receivable.code,
                debit=total_amount,
                credit=Decimal("0.00"),
            )
        )
        self.db.add(
            JournalEntryLine(
                journal_entry_id=journal.id,
                account_code=revenue.code,
                debit=Decimal("0.00"),
                credit=total_amount,
            )
        )

        invoice.status = InvoiceStatus.ISSUED.value
        self.db.add(invoice)
        self.db.commit()
        self.db.refresh(invoice)
        self._record_status_event(invoice, InvoiceStatus.DRAFT.value, InvoiceStatus.ISSUED.value, "issued")
        return invoice
