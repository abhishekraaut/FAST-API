from __future__ import annotations

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.database.base import Base
from app.models.organization import Organization
from app.schemas.account import AccountCreate
from app.schemas.accounting import JournalEntryCreate
from app.services.account_service import AccountService
from app.services.accounting_service import AccountingService


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


def test_account_creation_and_journal_posting(session: Session) -> None:
    org = Organization(name="Acme", slug="acme", currency="INR")
    session.add(org)
    session.commit()
    session.refresh(org)

    account_service = AccountService(session)
    account_service.create(AccountCreate(code="1100", name="Cash", account_type="ASSET"), organization_id=org.id)
    account_service.create(AccountCreate(code="4000", name="Revenue", account_type="REVENUE"), organization_id=org.id)

    accounting_service = AccountingService(session)
    entry = accounting_service.post_journal_entry(
        JournalEntryCreate(
            description="Revenue recognized",
            lines=[
                {"account_code": "1100", "debit": "100.00"},
                {"account_code": "4000", "credit": "100.00"},
            ],
        ),
        organization_id=org.id,
    )

    assert entry.description == "Revenue recognized"
    assert entry.lines[0].debit == "100.00"
    assert entry.lines[1].credit == "100.00"


def test_unbalanced_journal_entry_is_rejected(session: Session) -> None:
    org = Organization(name="Acme", slug="acme2", currency="INR")
    session.add(org)
    session.commit()
    session.refresh(org)

    account_service = AccountService(session)
    account_service.create(AccountCreate(code="1100", name="Cash", account_type="ASSET"), organization_id=org.id)
    account_service.create(AccountCreate(code="4000", name="Revenue", account_type="REVENUE"), organization_id=org.id)

    accounting_service = AccountingService(session)

    try:
        accounting_service.post_journal_entry(
            JournalEntryCreate(
                description="Broken entry",
                lines=[
                    {"account_code": "1100", "debit": "100.00"},
                    {"account_code": "4000", "credit": "90.00"},
                ],
            ),
            organization_id=org.id,
        )
    except ValueError:
        pass
    else:
        raise AssertionError("Expected ValueError for unbalanced journal entry")
