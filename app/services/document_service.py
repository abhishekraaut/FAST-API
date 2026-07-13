from __future__ import annotations

import hashlib
from decimal import Decimal
from pathlib import Path
from uuid import uuid4

from sqlalchemy.orm import Session

from app.core.exceptions import ValidationError, ResourceNotFoundError
from app.models.document import Document
from app.repositories.document_repo import DocumentRepository
from app.schemas.document import DocumentCreate, DocumentOut
from app.ocr.tesseract_provider import TesseractProvider
from app.ai.groq_provider import GroqProvider
from app.models.account import Account as ORMAccount
from app.services.accounting_service import AccountingService
from app.schemas.accounting import JournalEntryCreate


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

    def get(self, document_id: int, organization_id: int) -> Document:
        doc = self.repo.session.query(Document).filter(
            Document.id == document_id,
            Document.organization_id == organization_id
        ).first()
        if not doc:
            raise ResourceNotFoundError(f"Document with ID {document_id} not found")
        return doc

    def update_extraction(self, document_id: int, organization_id: int, extracted_data: dict) -> DocumentOut:
        doc = self.get(document_id, organization_id)
        doc.extracted_data = extracted_data
        doc.status = "processed"
        updated = self.repo.update(doc)
        return DocumentOut.model_validate(updated)

    def process_document_background(self, document_id: int) -> None:
        doc = self.repo.session.query(Document).filter(Document.id == document_id).first()
        if not doc:
            return

        doc.status = "processing"
        self.repo.update(doc)

        try:
            ocr = TesseractProvider()
            ocr_text = ocr.extract_text(doc.storage_path)

            ai = GroqProvider()
            extracted = ai.extract_structured(ocr_text)

            doc.ocr_text = ocr_text
            doc.extracted_data = extracted
            doc.status = "extracted"
            self.repo.update(doc)
        except Exception as exc:
            doc.status = "failed"
            doc.error_message = str(exc)
            self.repo.update(doc)

    def approve(self, document_id: int, organization_id: int) -> dict:
        doc = self.get(document_id, organization_id)
        if doc.status not in ["extracted", "processed", "uploaded"]:
            raise ValidationError(f"Document cannot be approved in status: {doc.status}")

        extracted = doc.extracted_data or {}
        doc_type = doc.document_type.lower()

        total_str = extracted.get("total") or "0.00"
        try:
            total = Decimal(str(total_str))
        except Exception:
            total = Decimal("0.00")

        if total <= Decimal("0.00"):
            amount_str = extracted.get("amount") or "0.00"
            try:
                total = Decimal(str(amount_str))
            except Exception:
                total = Decimal("0.00")

        if total <= Decimal("0.00"):
            raise ValidationError("Cannot approve document with zero or missing total amount.")

        db = self.repo.session

        if "invoice" in doc_type:
            ar_code = "1100"
            rev_code = "4000"

            ar_acc = db.query(ORMAccount).filter(ORMAccount.organization_id == organization_id, ORMAccount.code == ar_code).first()
            if not ar_acc:
                ar_acc = ORMAccount(organization_id=organization_id, code=ar_code, name="Accounts Receivable", account_type="ASSET")
                db.add(ar_acc)

            rev_acc = db.query(ORMAccount).filter(ORMAccount.organization_id == organization_id, ORMAccount.code == rev_code).first()
            if not rev_acc:
                rev_acc = ORMAccount(organization_id=organization_id, code=rev_code, name="Revenue", account_type="REVENUE")
                db.add(rev_acc)

            db.commit()

            acct_svc = AccountingService(db)
            je_payload = JournalEntryCreate(
                description=f"Approved Invoice: {extracted.get('invoice_number', 'N/A')} from {extracted.get('vendor_name', 'N/A')}",
                lines=[
                    {"account_code": ar_code, "debit": str(total), "credit": "0.00"},
                    {"account_code": rev_code, "debit": "0.00", "credit": str(total)}
                ]
            )
            je = acct_svc.post_journal_entry(je_payload, organization_id=organization_id)
            doc.status = "posted"
            self.repo.update(doc)
            return {"journal_entry_id": je.id, "status": "posted"}

        else:
            exp_code = "5000"
            cash_code = "1100"

            exp_acc = db.query(ORMAccount).filter(ORMAccount.organization_id == organization_id, ORMAccount.code == exp_code).first()
            if not exp_acc:
                exp_acc = ORMAccount(organization_id=organization_id, code=exp_code, name="Office Expenses", account_type="EXPENSE")
                db.add(exp_acc)

            cash_acc = db.query(ORMAccount).filter(ORMAccount.organization_id == organization_id, ORMAccount.code == cash_code).first()
            if not cash_acc:
                cash_acc = ORMAccount(organization_id=organization_id, code=cash_code, name="Cash", account_type="ASSET")
                db.add(cash_acc)

            db.commit()

            acct_svc = AccountingService(db)
            je_payload = JournalEntryCreate(
                description=f"Approved Expense receipt: {extracted.get('vendor_name', 'N/A')}",
                lines=[
                    {"account_code": exp_code, "debit": str(total), "credit": "0.00"},
                    {"account_code": cash_code, "debit": "0.00", "credit": str(total)}
                ]
            )
            je = acct_svc.post_journal_entry(je_payload, organization_id=organization_id)
            doc.status = "posted"
            self.repo.update(doc)
            return {"journal_entry_id": je.id, "status": "posted"}

    def _safe_filename(self, filename: str) -> str:
        import re
        suffix = Path(filename).suffix.lower() or ".bin"
        base = Path(filename).stem
        base_clean = re.sub(r'[^a-zA-Z0-9_\-]', '', base)[:30]
        digest = hashlib.sha256(filename.encode("utf-8")).hexdigest()[:12]
        return f"{base_clean}-{uuid4().hex[:8]}-{digest}{suffix}"

