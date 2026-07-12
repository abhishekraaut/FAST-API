from __future__ import annotations

from decimal import Decimal

from sqlalchemy.orm import Session

from app.core.exceptions import InvalidAccountingEntryError
from app.domain.accounting.entities import JournalEntry, JournalEntryLine
from app.domain.accounting.rules import validate_journal_entry
from app.models.account import Account
from app.models.journal_entry import JournalEntry as ORMJournalEntry
from app.models.journal_entry_line import JournalEntryLine as ORMJournalEntryLine
from app.repositories.account_repo import AccountRepository
from app.repositories.journal_entry_repo import JournalEntryRepository
from app.schemas.accounting import JournalEntryCreate, JournalEntryOut


class AccountingService:
    def __init__(self, session: Session) -> None:
        self.session = session
        self.account_repo = AccountRepository(session)
        self.journal_repo = JournalEntryRepository(session)

    def post_journal_entry(self, payload: JournalEntryCreate, organization_id: int) -> JournalEntryOut:
        domain_entry = JournalEntry(
            description=payload.description,
            lines=[
                JournalEntryLine(
                    account_code=line.account_code,
                    debit=Decimal(line.debit or "0.00"),
                    credit=Decimal(line.credit or "0.00"),
                )
                for line in payload.lines
            ],
        )
        validate_journal_entry(domain_entry)

        account_codes = {line.account_code for line in domain_entry.lines}
        for code in account_codes:
            if not self.account_repo.get_by_code_and_org(organization_id, code):
                raise InvalidAccountingEntryError(f"Unknown account code: {code}")

        orm_entry = ORMJournalEntry(organization_id=organization_id, description=payload.description, status="posted")
        orm_entry = self.journal_repo.create(orm_entry)

        orm_lines = []
        for line in domain_entry.lines:
            orm_line = ORMJournalEntryLine(
                journal_entry_id=orm_entry.id,
                account_code=line.account_code,
                debit=Decimal(line.debit),
                credit=Decimal(line.credit),
            )
            self.session.add(orm_line)
            orm_lines.append(orm_line)

        self.session.commit()
        self.session.refresh(orm_entry)
        return JournalEntryOut(
            id=orm_entry.id,
            organization_id=orm_entry.organization_id,
            description=orm_entry.description,
            status=orm_entry.status,
            lines=[
                {
                    "account_code": line.account_code,
                    "debit": str(line.debit),
                    "credit": str(line.credit),
                }
                for line in orm_lines
            ],
        )
