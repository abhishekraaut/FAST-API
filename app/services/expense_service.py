from __future__ import annotations

from decimal import Decimal

from sqlalchemy.orm import Session

from datetime import datetime, timezone

from app.core.statuses import ExpenseStatus
from app.models.expense import Expense
from app.models.status_event import StatusEvent
from app.schemas.expense import ExpenseCreate


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
