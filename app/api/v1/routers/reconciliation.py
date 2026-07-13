from fastapi import APIRouter, Depends, Query, Path
from sqlalchemy.orm import Session

from app.api.v1.deps import get_db
from app.core.exceptions import http_exception_from_error
from app.schemas.reconciliation import (
    BankAccountCreate,
    BankAccountOut,
    BankTransactionCreate,
    BankTransactionOut,
    ReconciliationMatchRequest,
)
from app.services.reconciliation_service import ReconciliationService

router = APIRouter(prefix="/reconciliation", tags=["reconciliation"])


@router.post("/bank-accounts", response_model=BankAccountOut)
def create_bank_account(
    payload: BankAccountCreate,
    organization_id: int = Query(...),
    db: Session = Depends(get_db)
) -> BankAccountOut:
    try:
        acc = ReconciliationService(db).create_bank_account(organization_id, payload)
        return BankAccountOut.model_validate(acc)
    except Exception as exc:
        raise http_exception_from_error(exc) from exc


@router.get("/bank-accounts", response_model=list[BankAccountOut])
def list_bank_accounts(
    organization_id: int = Query(...),
    db: Session = Depends(get_db)
) -> list[BankAccountOut]:
    try:
        accs = ReconciliationService(db).list_bank_accounts(organization_id)
        return [BankAccountOut.model_validate(a) for a in accs]
    except Exception as exc:
        raise http_exception_from_error(exc) from exc


@router.post("/bank-accounts/{bank_account_id}/transactions", response_model=BankTransactionOut)
def create_bank_transaction(
    bank_account_id: int = Path(...),
    payload: BankTransactionCreate = None,
    organization_id: int = Query(...),
    db: Session = Depends(get_db),
) -> BankTransactionOut:
    try:
        if not payload:
            raise ValueError("Payload is required")
        tx = ReconciliationService(db).create_bank_transaction(organization_id, bank_account_id, payload)
        return BankTransactionOut.model_validate(tx)
    except Exception as exc:
        raise http_exception_from_error(exc) from exc


@router.get("/bank-accounts/{bank_account_id}/transactions", response_model=list[BankTransactionOut])
def list_bank_transactions(
    bank_account_id: int = Path(...),
    status: str | None = Query(None),
    organization_id: int = Query(...),
    db: Session = Depends(get_db),
) -> list[BankTransactionOut]:
    try:
        txs = ReconciliationService(db).list_transactions(organization_id, bank_account_id, status)
        return [BankTransactionOut.model_validate(t) for t in txs]
    except Exception as exc:
        raise http_exception_from_error(exc) from exc


@router.post("/transactions/{transaction_id}/match", response_model=BankTransactionOut)
def manual_match(
    transaction_id: int = Path(...),
    payload: ReconciliationMatchRequest = None,
    organization_id: int = Query(...),
    db: Session = Depends(get_db),
) -> BankTransactionOut:
    try:
        if not payload:
            raise ValueError("Payload is required")
        tx = ReconciliationService(db).manual_match(organization_id, transaction_id, payload.journal_entry_id)
        return BankTransactionOut.model_validate(tx)
    except Exception as exc:
        raise http_exception_from_error(exc) from exc


@router.post("/bank-accounts/{bank_account_id}/auto-reconcile")
def auto_reconcile(
    bank_account_id: int = Path(...),
    organization_id: int = Query(...),
    db: Session = Depends(get_db),
) -> dict:
    try:
        matched_count = ReconciliationService(db).auto_reconcile(organization_id, bank_account_id)
        return {"matched_count": matched_count}
    except Exception as exc:
        raise http_exception_from_error(exc) from exc
