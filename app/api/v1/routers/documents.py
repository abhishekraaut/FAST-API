from fastapi import APIRouter, Depends, File, Query, UploadFile, BackgroundTasks
from sqlalchemy.orm import Session

from app.api.v1.deps import get_db
from app.core.exceptions import http_exception_from_error
from app.schemas.document import DocumentCreate, DocumentOut
from app.services.document_service import DocumentService

router = APIRouter(prefix="/documents", tags=["documents"])


@router.post("/upload", response_model=DocumentOut)
def upload_document(
    background_tasks: BackgroundTasks,
    organization_id: int = Query(...),
    document_type: str = "invoice",
    description: str | None = None,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
) -> DocumentOut:
    try:
        payload = DocumentCreate(document_type=document_type, description=description)
        contents = file.file.read()
        service = DocumentService(db)
        doc_out = service.create_from_upload(
            organization_id=organization_id,
            payload=payload,
            filename=file.filename or "upload.bin",
            content_type=file.content_type or "application/octet-stream",
            file_bytes=contents,
        )
        # Queue OCR and AI extraction pipeline in the background
        background_tasks.add_task(service.process_document_background, doc_out.id)
        return doc_out
    except Exception as exc:
        raise http_exception_from_error(exc) from exc


@router.get("", response_model=list[DocumentOut])
def list_documents(organization_id: int = Query(...), db: Session = Depends(get_db)) -> list[DocumentOut]:
    try:
        return DocumentService(db).list_for_organization(organization_id)
    except Exception as exc:
        raise http_exception_from_error(exc) from exc


@router.get("/{document_id}", response_model=DocumentOut)
def get_document(
    document_id: int,
    organization_id: int = Query(...),
    db: Session = Depends(get_db),
) -> DocumentOut:
    try:
        doc = DocumentService(db).get(document_id, organization_id)
        return DocumentOut.model_validate(doc)
    except Exception as exc:
        raise http_exception_from_error(exc) from exc


@router.patch("/{document_id}/extraction", response_model=DocumentOut)
def update_document_extraction(
    document_id: int,
    payload: dict,
    organization_id: int = Query(...),
    db: Session = Depends(get_db),
) -> DocumentOut:
    try:
        return DocumentService(db).update_extraction(document_id, organization_id, payload)
    except Exception as exc:
        raise http_exception_from_error(exc) from exc


@router.post("/{document_id}/approve")
def approve_document(
    document_id: int,
    organization_id: int = Query(...),
    db: Session = Depends(get_db),
) -> dict:
    try:
        return DocumentService(db).approve(document_id, organization_id)
    except Exception as exc:
        raise http_exception_from_error(exc) from exc
