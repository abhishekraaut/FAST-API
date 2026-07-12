from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.v1.deps import get_db
from app.core.exceptions import http_exception_from_error
from app.schemas.accounting import JournalEntryCreate, JournalEntryOut
from app.services.accounting_service import AccountingService

router = APIRouter(prefix="/ledger", tags=["ledger"])


@router.post("/journal-entries", response_model=JournalEntryOut)
def post_journal_entry(payload: JournalEntryCreate, organization_id: int = Query(...), db: Session = Depends(get_db)) -> JournalEntryOut:
    try:
        return AccountingService(db).post_journal_entry(payload, organization_id=organization_id)
    except Exception as exc:
        raise http_exception_from_error(exc) from exc
