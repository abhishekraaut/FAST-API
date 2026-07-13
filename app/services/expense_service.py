from __future__ import annotations

from decimal import Decimal

from sqlalchemy.orm import Session

from datetime import datetime, timezone

from app.core.statuses import ExpenseStatus
from app.models.expense import Expense
from app.models.status_event import StatusEvent
from app.schemas.expense import ExpenseCreate
from app.models.account import Account
from app.models.journal_entry import JournalEntry
from app.models.journal_entry_line import JournalEntryLine



class ExpenseService:
    def __init__(self, db: Session):
        self.db = db

    def create(self, payload: ExpenseCreate, organization_id: int) -> Expense:
        expense = Expense(
            organization_id=organization_id,
            vendor_name=payload.vendor_name,
            description=payload.description,
            amount=format(Decimal(str(payload.amount)), ".2f"),
            status=ExpenseStatus.DRAFT.value,
        )
        self.db.add(expense)
        self.db.commit()
        self.db.refresh(expense)
        self._record_status_event(expense, None, ExpenseStatus.DRAFT.value, "created")
        return expense

    def list(self, organization_id: int) -> list[Expense]:
        return self.db.query(Expense).filter(Expense.organization_id == organization_id).order_by(Expense.id.desc()).all()

    def get(self, expense_id: int, organization_id: int) -> Expense:
        expense = self.db.query(Expense).filter(Expense.id == expense_id, Expense.organization_id == organization_id).first()
        if not expense:
            raise ValueError("Expense not found")
        return expense

    def _record_status_event(self, expense: Expense, from_status: str | None, to_status: str, reason: str) -> None:
        event = StatusEvent(
            organization_id=expense.organization_id,
            entity_type="expense",
            entity_id=expense.id,
            from_status=from_status,
            to_status=to_status,
            reason=reason,
            created_at=datetime.now(timezone.utc).isoformat(),
        )
        self.db.add(event)
        self.db.commit()

    def approve(self, expense_id: int, organization_id: int) -> Expense:
        expense = self.db.query(Expense).filter(Expense.id == expense_id, Expense.organization_id == organization_id).first()
        if not expense:
            raise ValueError("Expense not found")

        expense.status = ExpenseStatus.APPROVED.value
        self.db.add(expense)
        self.db.commit()
        self.db.refresh(expense)
        self._record_status_event(expense, ExpenseStatus.DRAFT.value, ExpenseStatus.APPROVED.value, "approved")
        return expense
    def reject(self, expense_id: int, organization_id: int) -> Expense:
        expense = self.db.query(Expense).filter(Expense.id == expense_id, Expense.organization_id == organization_id).first()
        if not expense:
            raise ValueError("Expense not found")

        expense.status = ExpenseStatus.REJECTED.value
        self.db.add(expense)
        self.db.commit()
        self.db.refresh(expense)
        self._record_status_event(expense, ExpenseStatus.DRAFT.value, ExpenseStatus.REJECTED.value, "rejected")
        return expense

    def pay(self, expense_id: int, organization_id: int) -> Expense:
        expense = self.db.query(Expense).filter(Expense.id == expense_id, Expense.organization_id == organization_id).first()
        if not expense:
            raise ValueError("Expense not found")

        if expense.status not in [ExpenseStatus.APPROVED.value, ExpenseStatus.DRAFT.value]:
            raise ValueError(f"Expense cannot be paid in status: {expense.status}")

        exp_acc = self.db.query(Account).filter(Account.organization_id == organization_id, Account.code == "5000").first()
        if not exp_acc:
            exp_acc = Account(organization_id=organization_id, code="5000", name="Office Expenses", account_type="EXPENSE")
            self.db.add(exp_acc)

        cash_acc = self.db.query(Account).filter(
            Account.organization_id == organization_id,
            (Account.code == "1101") | (Account.name.like("%Cash%")) | (Account.name.like("%Bank%"))
        ).first()
        if not cash_acc:
            cash_acc = Account(organization_id=organization_id, code="1101", name="Cash at Bank", account_type="ASSET")
            self.db.add(cash_acc)

        self.db.flush()

        journal = JournalEntry(
            organization_id=organization_id,
            description=f"Paid Expense: {expense.vendor_name} - {expense.description or ''}",
            status="posted",
        )
        self.db.add(journal)
        self.db.flush()

        amount_val = Decimal(str(expense.amount))
        self.db.add(
            JournalEntryLine(
                journal_entry_id=journal.id,
                account_code=exp_acc.code,
                debit=amount_val,
                credit=Decimal("0.00"),
            )
        )
        self.db.add(
            JournalEntryLine(
                journal_entry_id=journal.id,
                account_code=cash_acc.code,
                debit=Decimal("0.00"),
                credit=amount_val,
            )
        )

        old_status = expense.status
        expense.status = ExpenseStatus.PAID.value
        self.db.add(expense)
        self.db.commit()
        self.db.refresh(expense)
        self._record_status_event(expense, old_status, ExpenseStatus.PAID.value, "paid")
        return expense

