from __future__ import annotations

from decimal import Decimal
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.database.base import Base
from app.models.organization import Organization
from app.schemas.reconciliation import BankAccountCreate, BankTransactionCreate
from app.services.reconciliation_service import ReconciliationService
from app.services.account_service import AccountService
from app.services.accounting_service import AccountingService
from app.schemas.account import AccountCreate
from app.schemas.accounting import JournalEntryCreate


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


def test_bank_reconciliation_flow(session: Session) -> None:
    org = Organization(name="Recon Org", slug="recon-org", currency="INR")
    session.add(org)
    session.commit()
    session.refresh(org)

    account_svc = AccountService(session)
    accounting_svc = AccountingService(session)
    recon_svc = ReconciliationService(session)

    # 1. Create Chart of accounts
    account_svc.create(AccountCreate(code="1100", name="Receivables", account_type="ASSET"), organization_id=org.id)
    account_svc.create(AccountCreate(code="4000", name="Revenue", account_type="REVENUE"), organization_id=org.id)
    session.commit()

    # 2. Post a journal entry (which we want to match)
    je = accounting_svc.post_journal_entry(
        JournalEntryCreate(
            description="Consulting Revenue",
            lines=[
                {"account_code": "1100", "debit": "5000.00", "credit": "0.00"},
                {"account_code": "4000", "debit": "0.00", "credit": "5000.00"},
            ],
        ),
        organization_id=org.id,
    )

    # 3. Create a Bank Account
    bank_acc = recon_svc.create_bank_account(
        organization_id=org.id,
        payload=BankAccountCreate(name="HDFC Operating Account", account_number="9876543210"),
    )
    assert bank_acc.id is not None
    assert bank_acc.name == "HDFC Operating Account"

    # 4. Create Bank Transactions
    tx = recon_svc.create_bank_transaction(
        organization_id=org.id,
        bank_account_id=bank_acc.id,
        payload=BankTransactionCreate(
            transaction_date="2026-07-12",
            description="Deposit from Client XYZ",
            amount="5000.00",
        ),
    )
    assert tx.id is not None
    assert tx.status == "unmatched"

    # 5. Perform auto reconciliation
    matched_count = recon_svc.auto_reconcile(organization_id=org.id, bank_account_id=bank_acc.id)
    assert matched_count == 1

    # Reload transaction and verify status is matched
    tx_reloaded = recon_svc.list_transactions(org.id, bank_acc.id)[0]
    assert tx_reloaded.status == "matched"
    assert tx_reloaded.matched_journal_entry_id == je.id
