from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.v1.deps import get_db
from app.schemas.invoice import InvoiceCreate, InvoiceOut
from app.services.invoice_service import InvoiceService

router = APIRouter(prefix="/invoices", tags=["invoices"])


@router.post("", response_model=InvoiceOut)
def create_invoice(payload: InvoiceCreate, db: Session = Depends(get_db)) -> InvoiceOut:
    service = InvoiceService(db)
    invoice = service.create(payload, organization_id=1)
    return InvoiceOut.model_validate(invoice)


@router.get("", response_model=list[InvoiceOut])
def list_invoices(organization_id: int = Query(...), db: Session = Depends(get_db)) -> list[InvoiceOut]:
    service = InvoiceService(db)
    invoices = service.list(organization_id=organization_id)
    return [InvoiceOut.model_validate(invoice) for invoice in invoices]


@router.get("/{invoice_id}", response_model=InvoiceOut)
def get_invoice(invoice_id: int, organization_id: int = Query(...), db: Session = Depends(get_db)) -> InvoiceOut:
    service = InvoiceService(db)
    try:
        invoice = service.get(invoice_id, organization_id=organization_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return InvoiceOut.model_validate(invoice)


@router.post("/{invoice_id}/cancel", response_model=InvoiceOut)
def cancel_invoice(invoice_id: int, db: Session = Depends(get_db)) -> InvoiceOut:
    service = InvoiceService(db)
    try:
        invoice = service.cancel(invoice_id, organization_id=1)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return InvoiceOut.model_validate(invoice)


@router.post("/{invoice_id}/issue", response_model=InvoiceOut)
def issue_invoice(invoice_id: int, db: Session = Depends(get_db)) -> InvoiceOut:
    service = InvoiceService(db)
    try:
        invoice = service.issue(invoice_id, organization_id=1)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return InvoiceOut.from_orm(invoice)
