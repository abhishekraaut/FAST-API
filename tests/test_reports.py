from __future__ import annotations

from decimal import Decimal
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.database.base import Base
from app.models.organization import Organization
from app.schemas.account import AccountCreate
from app.schemas.accounting import JournalEntryCreate
from app.services.account_service import AccountService
from app.services.accounting_service import AccountingService
from app.services.report_service import ReportService
from app.services.expense_service import ExpenseService
from app.schemas.expense import ExpenseCreate


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


def test_financial_reports_calculations(session: Session) -> None:
    org = Organization(name="Fin Org", slug="fin-org", currency="INR")
    session.add(org)
    session.commit()
    session.refresh(org)

    account_svc = AccountService(session)
    accounting_svc = AccountingService(session)
    report_svc = ReportService(session)
    expense_svc = ExpenseService(session)

    # 1. Setup Chart of Accounts
    # Asset, Revenue, Expense, GST accounts
    account_svc.create(AccountCreate(code="1100", name="Cash", account_type="ASSET"), organization_id=org.id)
    account_svc.create(AccountCreate(code="4000", name="Consulting Income", account_type="REVENUE"), organization_id=org.id)
    account_svc.create(AccountCreate(code="5000", name="Office Supplies Expense", account_type="EXPENSE"), organization_id=org.id)
    account_svc.create(AccountCreate(code="2200", name="Output CGST 9%", account_type="LIABILITY"), organization_id=org.id)

    # 2. Post a journal entry for consulting income + GST (CGST)
    accounting_svc.post_journal_entry(
        JournalEntryCreate(
            description="Consulting Project recognition with GST",
            lines=[
                {"account_code": "1100", "debit": "1090.00", "credit": "0.00"},  # Bank/Cash receives total
                {"account_code": "4000", "debit": "0.00", "credit": "1000.00"},  # Revenue
                {"account_code": "2200", "debit": "0.00", "credit": "90.00"},    # GST Liability
            ],
        ),
        organization_id=org.id,
    )

    # 3. Create a vendor expense
    expense_svc.create(
        ExpenseCreate(vendor_name="Paper Co", amount="150.00", description="Stationery invoice"),
        organization_id=org.id,
    )

    # 4. Generate Reports and assert balances
    trial_balance = report_svc.get_trial_balance(org.id)
    assert len(trial_balance) == 4
    # Cash account code 1100 net balance
    cash_rep = next(r for r in trial_balance if r["code"] == "1100")
    assert cash_rep["debit"] == "1090.00"
    assert cash_rep["balance"] == "1090.00"

    # Profit & Loss
    pl = report_svc.get_profit_loss(org.id)
    assert pl["total_revenue"] == "1000.00"
    assert pl["total_expenses"] == "0.00"  # No posted journal entries for expense account yet
    assert pl["net_profit"] == "1000.00"

    # GST Report
    gst = report_svc.get_gst_report(org.id)
    assert len(gst["details"]) == 1
    assert gst["total_gst_liability"] == "90.00"

    # Expenses Summary (uses Expense model)
    exp_summary = report_svc.get_expenses_summary(org.id)
    assert len(exp_summary["expenses"]) == 1
    assert exp_summary["total_amount"] == "150.00"
