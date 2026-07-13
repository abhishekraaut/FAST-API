from fastapi import APIRouter, Depends, Query, Path
from sqlalchemy.orm import Session

from app.api.v1.deps import get_db
from app.core.exceptions import http_exception_from_error
from app.schemas.invoice import InvoiceCreate, InvoiceOut
from app.services.invoice_service import InvoiceService

router = APIRouter(prefix="/invoices", tags=["invoices"])


@router.post("", response_model=InvoiceOut)
def create_invoice(payload: InvoiceCreate, db: Session = Depends(get_db)) -> InvoiceOut:
    try:
        invoice = InvoiceService(db).create(payload, organization_id=1)
        return InvoiceOut.model_validate(invoice)
    except Exception as exc:
        raise http_exception_from_error(exc) from exc


@router.get("", response_model=list[InvoiceOut])
def list_invoices(organization_id: int = Query(...), db: Session = Depends(get_db)) -> list[InvoiceOut]:
    try:
        invoices = InvoiceService(db).list(organization_id=organization_id)
        return [InvoiceOut.model_validate(invoice) for invoice in invoices]
    except Exception as exc:
        raise http_exception_from_error(exc) from exc


@router.get("/{invoice_id}", response_model=InvoiceOut)
def get_invoice(
    invoice_id: int = Path(...),
    organization_id: int = Query(...),
    db: Session = Depends(get_db)
) -> InvoiceOut:
    try:
        invoice = InvoiceService(db).get(invoice_id, organization_id=organization_id)
        return InvoiceOut.model_validate(invoice)
    except Exception as exc:
        raise http_exception_from_error(exc) from exc


@router.post("/{invoice_id}/cancel", response_model=InvoiceOut)
def cancel_invoice(invoice_id: int = Path(...), db: Session = Depends(get_db)) -> InvoiceOut:
    try:
        invoice = InvoiceService(db).cancel(invoice_id, organization_id=1)
        return InvoiceOut.model_validate(invoice)
    except Exception as exc:
        raise http_exception_from_error(exc) from exc


@router.post("/{invoice_id}/issue", response_model=InvoiceOut)
def issue_invoice(invoice_id: int = Path(...), db: Session = Depends(get_db)) -> InvoiceOut:
    try:
        invoice = InvoiceService(db).issue(invoice_id, organization_id=1)
        return InvoiceOut.model_validate(invoice)
    except Exception as exc:
        raise http_exception_from_error(exc) from exc


@router.post("/{invoice_id}/pay", response_model=InvoiceOut)
def pay_invoice(
    invoice_id: int = Path(...),
    organization_id: int = Query(1),
    db: Session = Depends(get_db)
) -> InvoiceOut:
    try:
        invoice = InvoiceService(db).pay(invoice_id, organization_id=organization_id)
        return InvoiceOut.model_validate(invoice)
    except Exception as exc:
        raise http_exception_from_error(exc) from exc
