from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.v1.deps import get_db
from app.core.exceptions import http_exception_from_error
from app.schemas.vendor import VendorCreate, VendorOut
from app.services.vendor_service import VendorService

router = APIRouter(prefix="/vendors", tags=["vendors"])


@router.post("", response_model=VendorOut)
def create_vendor(payload: VendorCreate, db: Session = Depends(get_db)) -> VendorOut:
    try:
        return VendorService(db).create(payload, organization_id=payload.organization_id)
    except Exception as exc:
        raise http_exception_from_error(exc) from exc


@router.get("", response_model=list[VendorOut])
def list_vendors(organization_id: int = Query(...), q: str | None = None, db: Session = Depends(get_db)) -> list[VendorOut]:
    try:
        return VendorService(db).list(organization_id=organization_id, q=q)
    except Exception as exc:
        raise http_exception_from_error(exc) from exc
