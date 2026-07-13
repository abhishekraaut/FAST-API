from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.v1.deps import get_db
from app.core.exceptions import http_exception_from_error
from app.services.report_service import ReportService

router = APIRouter(prefix="/reports", tags=["reports"])


@router.get("/trial-balance")
def get_trial_balance(organization_id: int = Query(...), db: Session = Depends(get_db)) -> list[dict]:
    try:
        return ReportService(db).get_trial_balance(organization_id)
    except Exception as exc:
        raise http_exception_from_error(exc) from exc


@router.get("/profit-loss")
def get_profit_loss(organization_id: int = Query(...), db: Session = Depends(get_db)) -> dict:
    try:
        return ReportService(db).get_profit_loss(organization_id)
    except Exception as exc:
        raise http_exception_from_error(exc) from exc


@router.get("/expenses")
def get_expenses_report(organization_id: int = Query(...), db: Session = Depends(get_db)) -> dict:
    try:
        return ReportService(db).get_expenses_summary(organization_id)
    except Exception as exc:
        raise http_exception_from_error(exc) from exc


@router.get("/gst")
def get_gst_report(organization_id: int = Query(...), db: Session = Depends(get_db)) -> dict:
    try:
        return ReportService(db).get_gst_report(organization_id)
    except Exception as exc:
        raise http_exception_from_error(exc) from exc


@router.get("/tds")
def get_tds_report(organization_id: int = Query(...), db: Session = Depends(get_db)) -> dict:
    try:
        return ReportService(db).get_tds_report(organization_id)
    except Exception as exc:
        raise http_exception_from_error(exc) from exc
