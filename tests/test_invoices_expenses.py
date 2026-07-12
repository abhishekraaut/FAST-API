from __future__ import annotations

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.database.base import Base
from app.models.account import Account
from app.models.organization import Organization
from app.core.statuses import ExpenseStatus, InvoiceStatus
from app.models.status_event import StatusEvent
from app.schemas.expense import ExpenseCreate
from app.schemas.invoice import InvoiceCreate, InvoiceItemCreate
from app.services.account_service import AccountService
from app.services.expense_service import ExpenseService
from app.services.invoice_service import InvoiceService


@pytest.fixture()
def session() -> Session:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def test_invoice_issue_creates_accounting_entry(session: Session) -> None:
    org = Organization(name="Acme", slug="acme-invoice", currency="INR")
    session.add(org)
    session.commit()
    session.refresh(org)

    account_service = AccountService(session)
    account_service.create(type("Payload", (), {"code": "1100", "name": "Accounts Receivable", "account_type": "ASSET"})(), organization_id=org.id)
    account_service.create(type("Payload", (), {"code": "4000", "name": "Revenue", "account_type": "REVENUE"})(), organization_id=org.id)

    service = InvoiceService(session)
    invoice = service.create(
        InvoiceCreate(
            customer_name="Acme Client",
            due_date="2026-08-01",
            items=[InvoiceItemCreate(description="Service", quantity=1, unit_price="100.00")],
        ),
        organization_id=org.id,
    )
    issued = service.issue(invoice.id, organization_id=org.id)

    assert issued.status == InvoiceStatus.ISSUED.value
    assert issued.total == "100.00"


def test_expense_creation_tracks_status(session: Session) -> None:
    org = Organization(name="Acme", slug="acme-expense", currency="INR")
    session.add(org)
    session.commit()
    session.refresh(org)

    service = ExpenseService(session)
    expense = service.create(
        ExpenseCreate(
            vendor_name="Office Supplies",
            amount="50.00",
            description="Stationery",
        ),
        organization_id=org.id,
    )

    assert expense.status == ExpenseStatus.DRAFT.value
    assert expense.amount == "50.00"


def test_expense_approval_changes_status(session: Session) -> None:
    org = Organization(name="Acme", slug="acme-expense-approval", currency="INR")
    session.add(org)
    session.commit()
    session.refresh(org)

    service = ExpenseService(session)
    expense = service.create(
        ExpenseCreate(
            vendor_name="Cloud Service",
            amount="120.00",
            description="Monthly subscription",
        ),
        organization_id=org.id,
    )

    approved = service.approve(expense.id, organization_id=org.id)

    assert approved.status == ExpenseStatus.APPROVED.value


def test_invoice_and_expense_listing(session: Session) -> None:
    org = Organization(name="Acme", slug="acme-listing", currency="INR")
    session.add(org)
    session.commit()
    session.refresh(org)

    invoice_service = InvoiceService(session)
    invoice = invoice_service.create(
        InvoiceCreate(
            customer_name="Listed Client",
            due_date="2026-08-15",
            items=[InvoiceItemCreate(description="Consulting", quantity=1, unit_price="75.00")],
        ),
        organization_id=org.id,
    )

    expense_service = ExpenseService(session)
    expense_service.create(
        ExpenseCreate(
            vendor_name="Software Vendor",
            amount="30.00",
            description="Licensing",
        ),
        organization_id=org.id,
    )

    invoices = invoice_service.list(organization_id=org.id)
    expenses = expense_service.list(organization_id=org.id)

    assert len(invoices) == 1
    assert invoices[0].id == invoice.id
    assert len(expenses) == 1


def test_expense_rejection_changes_status(session: Session) -> None:
    org = Organization(name="Acme", slug="acme-reject", currency="INR")
    session.add(org)
    session.commit()
    session.refresh(org)

    service = ExpenseService(session)
    expense = service.create(
        ExpenseCreate(
            vendor_name="Rejected Vendor",
            amount="80.00",
            description="Needs review",
        ),
        organization_id=org.id,
    )

    rejected = service.reject(expense.id, organization_id=org.id)

    assert rejected.status == ExpenseStatus.REJECTED.value


def test_status_events_are_recorded_for_transitions(session: Session) -> None:
    org = Organization(name="Acme", slug="acme-history", currency="INR")
    session.add(org)
    session.commit()
    session.refresh(org)

    account_service = AccountService(session)
    account_service.create(type("Payload", (), {"code": "1100", "name": "Accounts Receivable", "account_type": "ASSET"})(), organization_id=org.id)
    account_service.create(type("Payload", (), {"code": "4000", "name": "Revenue", "account_type": "REVENUE"})(), organization_id=org.id)

    invoice_service = InvoiceService(session)
    invoice = invoice_service.create(
        InvoiceCreate(
            customer_name="History Client",
            due_date="2026-11-01",
            items=[InvoiceItemCreate(description="Review", quantity=1, unit_price="10.00")],
        ),
        organization_id=org.id,
    )
    invoice_service.issue(invoice.id, organization_id=org.id)

    expense_service = ExpenseService(session)
    expense = expense_service.create(
        ExpenseCreate(vendor_name="History Vendor", amount="20.00", description="Audit"),
        organization_id=org.id,
    )
    expense_service.approve(expense.id, organization_id=org.id)

    events = session.query(StatusEvent).filter(StatusEvent.organization_id == org.id).all()

    assert len(events) >= 4


def test_invoice_and_expense_detail_retrieval(session: Session) -> None:
    org = Organization(name="Acme", slug="acme-detail", currency="INR")
    session.add(org)
    session.commit()
    session.refresh(org)

    invoice_service = InvoiceService(session)
    invoice = invoice_service.create(
        InvoiceCreate(
            customer_name="Detail Client",
            due_date="2026-09-01",
            items=[InvoiceItemCreate(description="Setup", quantity=1, unit_price="25.00")],
        ),
        organization_id=org.id,
    )

    expense_service = ExpenseService(session)
    expense = expense_service.create(
        ExpenseCreate(
            vendor_name="Detail Vendor",
            amount="12.50",
            description="Support",
        ),
        organization_id=org.id,
    )

    fetched_invoice = invoice_service.get(invoice.id, organization_id=org.id)
    fetched_expense = expense_service.get(expense.id, organization_id=org.id)

    assert fetched_invoice.id == invoice.id
    assert fetched_expense.id == expense.id


def test_invoice_cancellation_changes_status(session: Session) -> None:
    org = Organization(name="Acme", slug="acme-cancel", currency="INR")
    session.add(org)
    session.commit()
    session.refresh(org)

    service = InvoiceService(session)
    invoice = service.create(
        InvoiceCreate(
            customer_name="Cancelled Client",
            due_date="2026-10-01",
            items=[InvoiceItemCreate(description="Audit", quantity=1, unit_price="40.00")],
        ),
        organization_id=org.id,
    )

    canceled = service.cancel(invoice.id, organization_id=org.id)

    assert canceled.status == InvoiceStatus.CANCELLED.value
