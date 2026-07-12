from __future__ import annotations

import hashlib
from pathlib import Path
from uuid import uuid4

from sqlalchemy.orm import Session

from app.core.exceptions import ValidationError
from app.models.document import Document
from app.repositories.document_repo import DocumentRepository
from app.schemas.document import DocumentCreate, DocumentOut


class DocumentService:
    def __init__(self, session: Session, storage_dir: str | None = None) -> None:
        self.repo = DocumentRepository(session)
        self.storage_dir = Path(storage_dir or "uploads")
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.storage_dir = self.storage_dir.resolve()

    def create_from_upload(
        self,
        *,
        organization_id: int,
        payload: DocumentCreate,
        filename: str,
        content_type: str,
        file_bytes: bytes,
    ) -> DocumentOut:
        allowed_mimes = {"application/pdf", "image/png", "image/jpeg", "image/tiff"}
        if content_type not in allowed_mimes:
            raise ValidationError("Unsupported file type")
        if len(file_bytes) > 5 * 1024 * 1024:
            raise ValidationError("File exceeds maximum size of 5MB")

        safe_name = self._safe_filename(filename)
        destination = self.storage_dir / safe_name
        destination.write_bytes(file_bytes)

        document = Document(
            organization_id=organization_id,
            document_type=payload.document_type,
            filename=safe_name,
            content_type=content_type,
            storage_path=str(destination),
            status="uploaded",
            description=payload.description,
        )
        saved = self.repo.create(document)
        return DocumentOut.model_validate(saved)

    def list_for_organization(self, organization_id: int) -> list[DocumentOut]:
        documents = self.repo.list_for_organization(organization_id)
        return [DocumentOut.model_validate(document) for document in documents]

    def _safe_filename(self, filename: str) -> str:
        suffix = Path(filename).suffix.lower() or ".bin"
        digest = hashlib.sha256(filename.encode("utf-8")).hexdigest()[:12]
        return f"{uuid4().hex}-{digest}{suffix}"
