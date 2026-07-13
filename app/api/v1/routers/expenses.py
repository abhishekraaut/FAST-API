from fastapi import APIRouter, Depends, Query, Path
from sqlalchemy.orm import Session

from app.api.v1.deps import get_db
from app.core.exceptions import http_exception_from_error
from app.schemas.expense import ExpenseCreate, ExpenseOut
from app.services.expense_service import ExpenseService

router = APIRouter(prefix="/expenses", tags=["expenses"])


@router.post("", response_model=ExpenseOut)
def create_expense(payload: ExpenseCreate, db: Session = Depends(get_db)) -> ExpenseOut:
    try:
        expense = ExpenseService(db).create(payload, organization_id=1)
        return ExpenseOut.model_validate(expense)
    except Exception as exc:
        raise http_exception_from_error(exc) from exc


@router.get("", response_model=list[ExpenseOut])
def list_expenses(organization_id: int = Query(...), db: Session = Depends(get_db)) -> list[ExpenseOut]:
    try:
        expenses = ExpenseService(db).list(organization_id=organization_id)
        return [ExpenseOut.model_validate(expense) for expense in expenses]
    except Exception as exc:
        raise http_exception_from_error(exc) from exc


@router.get("/{expense_id}", response_model=ExpenseOut)
def get_expense(
    expense_id: int = Path(...),
    organization_id: int = Query(...),
    db: Session = Depends(get_db)
) -> ExpenseOut:
    try:
        expense = ExpenseService(db).get(expense_id, organization_id=organization_id)
        return ExpenseOut.model_validate(expense)
    except Exception as exc:
        raise http_exception_from_error(exc) from exc


@router.post("/{expense_id}/approve", response_model=ExpenseOut)
def approve_expense(expense_id: int = Path(...), db: Session = Depends(get_db)) -> ExpenseOut:
    try:
        expense = ExpenseService(db).approve(expense_id, organization_id=1)
        return ExpenseOut.model_validate(expense)
    except Exception as exc:
        raise http_exception_from_error(exc) from exc


@router.post("/{expense_id}/reject", response_model=ExpenseOut)
def reject_expense(expense_id: int = Path(...), db: Session = Depends(get_db)) -> ExpenseOut:
    try:
        expense = ExpenseService(db).reject(expense_id, organization_id=1)
        return ExpenseOut.model_validate(expense)
    except Exception as exc:
        raise http_exception_from_error(exc) from exc


@router.post("/{expense_id}/pay", response_model=ExpenseOut)
def pay_expense(
    expense_id: int = Path(...),
    organization_id: int = Query(1),
    db: Session = Depends(get_db)
) -> ExpenseOut:
    try:
        expense = ExpenseService(db).pay(expense_id, organization_id=organization_id)
        return ExpenseOut.model_validate(expense)
    except Exception as exc:
        raise http_exception_from_error(exc) from exc
