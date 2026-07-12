from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.v1.deps import get_db
from app.core.exceptions import http_exception_from_error
from app.schemas.client import ClientCreate, ClientOut
from app.services.client_service import ClientService

router = APIRouter(prefix="/clients", tags=["clients"])


@router.post("", response_model=ClientOut)
def create_client(payload: ClientCreate, db: Session = Depends(get_db)) -> ClientOut:
    try:
        return ClientService(db).create(payload, organization_id=payload.organization_id)
    except Exception as exc:
        raise http_exception_from_error(exc) from exc


@router.get("", response_model=list[ClientOut])
def list_clients(organization_id: int = Query(...), q: str | None = None, db: Session = Depends(get_db)) -> list[ClientOut]:
    try:
        return ClientService(db).list(organization_id=organization_id, q=q)
    except Exception as exc:
        raise http_exception_from_error(exc) from exc
