from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.v1.deps import get_db
from app.core.exceptions import http_exception_from_error
from app.schemas.account import AccountCreate, AccountOut
from app.services.account_service import AccountService

router = APIRouter(prefix="/accounts", tags=["accounts"])


@router.post("", response_model=AccountOut)
def create_account(payload: AccountCreate, organization_id: int = Query(...), db: Session = Depends(get_db)) -> AccountOut:
    try:
        return AccountService(db).create(payload, organization_id=organization_id)
    except Exception as exc:
        raise http_exception_from_error(exc) from exc


@router.get("", response_model=list[AccountOut])
def list_accounts(organization_id: int = Query(...), db: Session = Depends(get_db)) -> list[AccountOut]:
    try:
        return AccountService(db).list(organization_id=organization_id)
    except Exception as exc:
        raise http_exception_from_error(exc) from exc
