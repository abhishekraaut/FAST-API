from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.v1.deps import get_db
from app.core.exceptions import http_exception_from_error, InvalidAccountingEntryError
from app.domain.accounting.entities import JournalEntry, JournalEntryLine
from app.domain.accounting.rules import validate_journal_entry

router = APIRouter(prefix="/accounting", tags=["accounting"])


@router.post("/journal-entries")
def create_journal_entry(payload: dict[str, object], db: Session = Depends(get_db)) -> dict[str, object]:
    try:
        lines = [
            JournalEntryLine(
                account_code=str(line["account_code"]),
                debit=line.get("debit", 0),
                credit=line.get("credit", 0),
            )
            for line in payload.get("lines", [])
        ]
        entry = JournalEntry(description=str(payload.get("description", "")), lines=lines)
        validate_journal_entry(entry)
        return {"status": "posted", "description": entry.description, "lines": [line.__dict__ for line in entry.lines]}
    except Exception as exc:
        raise http_exception_from_error(exc) from exc
