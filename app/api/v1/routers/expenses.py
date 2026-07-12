from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.v1.deps import get_db
from app.schemas.expense import ExpenseCreate, ExpenseOut
from app.services.expense_service import ExpenseService

router = APIRouter(prefix="/expenses", tags=["expenses"])


@router.post("", response_model=ExpenseOut)
def create_expense(payload: ExpenseCreate, db: Session = Depends(get_db)) -> ExpenseOut:
    service = ExpenseService(db)
    expense = service.create(payload, organization_id=1)
    return ExpenseOut.model_validate(expense)


@router.get("", response_model=list[ExpenseOut])
def list_expenses(organization_id: int = Query(...), db: Session = Depends(get_db)) -> list[ExpenseOut]:
    service = ExpenseService(db)
    expenses = service.list(organization_id=organization_id)
    return [ExpenseOut.model_validate(expense) for expense in expenses]


@router.get("/{expense_id}", response_model=ExpenseOut)
def get_expense(expense_id: int, organization_id: int = Query(...), db: Session = Depends(get_db)) -> ExpenseOut:
    service = ExpenseService(db)
    try:
        expense = service.get(expense_id, organization_id=organization_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return ExpenseOut.model_validate(expense)


@router.post("/{expense_id}/approve", response_model=ExpenseOut)
def approve_expense(expense_id: int, db: Session = Depends(get_db)) -> ExpenseOut:
    service = ExpenseService(db)
    try:
        expense = service.approve(expense_id, organization_id=1)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return ExpenseOut.model_validate(expense)


@router.post("/{expense_id}/reject", response_model=ExpenseOut)
def reject_expense(expense_id: int, db: Session = Depends(get_db)) -> ExpenseOut:
    service = ExpenseService(db)
    try:
        expense = service.reject(expense_id, organization_id=1)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return ExpenseOut.model_validate(expense)
