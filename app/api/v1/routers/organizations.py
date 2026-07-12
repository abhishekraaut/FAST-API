from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.v1.deps import get_db
from app.core.exceptions import http_exception_from_error
from app.schemas.organization import OrganizationCreate, OrganizationOut
from app.services.organization_service import OrganizationService

router = APIRouter(prefix="/organizations", tags=["organizations"])


@router.post("", response_model=OrganizationOut)
def create_organization(payload: OrganizationCreate, db: Session = Depends(get_db)) -> OrganizationOut:
    try:
        return OrganizationService(db).create(payload)
    except Exception as exc:
        raise http_exception_from_error(exc) from exc
