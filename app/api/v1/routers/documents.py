from fastapi import APIRouter, Depends, File, Query, UploadFile
from sqlalchemy.orm import Session

from app.api.v1.deps import get_db
from app.core.exceptions import http_exception_from_error
from app.schemas.document import DocumentCreate, DocumentOut
from app.services.document_service import DocumentService

router = APIRouter(prefix="/documents", tags=["documents"])


@router.post("/upload", response_model=DocumentOut)
def upload_document(
    organization_id: int = Query(...),
    document_type: str = "invoice",
    description: str | None = None,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
) -> DocumentOut:
    try:
        payload = DocumentCreate(document_type=document_type, description=description)
        contents = file.file.read()
        return DocumentService(db).create_from_upload(
            organization_id=organization_id,
            payload=payload,
            filename=file.filename or "upload.bin",
            content_type=file.content_type or "application/octet-stream",
            file_bytes=contents,
        )
    except Exception as exc:
        raise http_exception_from_error(exc) from exc


@router.get("", response_model=list[DocumentOut])
def list_documents(organization_id: int = Query(...), db: Session = Depends(get_db)) -> list[DocumentOut]:
    try:
        return DocumentService(db).list_for_organization(organization_id)
    except Exception as exc:
        raise http_exception_from_error(exc) from exc
