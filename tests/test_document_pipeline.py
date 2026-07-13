from __future__ import annotations

from decimal import Decimal
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.database.base import Base
from app.models.organization import Organization
from app.schemas.document import DocumentCreate
from app.services.document_service import DocumentService
from app.models.document import Document
from app.models.journal_entry import JournalEntry
from app.models.journal_entry_line import JournalEntryLine


@pytest.fixture()
def session() -> Session:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def test_document_ocr_extraction_and_approval_flow(session: Session) -> None:
    org = Organization(name="Doc Org", slug="doc-org", currency="INR")
    session.add(org)
    session.commit()
    session.refresh(org)

    service = DocumentService(session)

    # 1. Create uploaded document
    doc = service.create_from_upload(
        organization_id=org.id,
        payload=DocumentCreate(document_type="invoice", description="Vendor invoice"),
        filename="invoice.pdf",
        content_type="application/pdf",
        file_bytes=b"%PDF-1.4\n% fake pdf",
    )
    assert doc.status == "uploaded"

    # 2. Simulate background task execution
    service.process_document_background(doc.id)

    db_doc = session.query(Document).filter(Document.id == doc.id).first()
    assert db_doc.status == "extracted"
    assert db_doc.ocr_text is not None
    assert db_doc.extracted_data is not None
    assert db_doc.extracted_data["vendor_name"] == "Amazon Web Services India"

    # 3. Simulate human-in-the-loop update to extraction details
    extracted = db_doc.extracted_data.copy()
    extracted["total"] = "12000.00"
    service.update_extraction(doc.id, org.id, extracted)

    db_doc_updated = session.query(Document).filter(Document.id == doc.id).first()
    assert db_doc_updated.status == "processed"
    assert db_doc_updated.extracted_data["total"] == "12000.00"

    # 4. Approve document (creates ledger entries)
    res = service.approve(doc.id, org.id)
    assert res["status"] == "posted"
    assert res["journal_entry_id"] is not None

    # Check journal entry and lines
    je = session.query(JournalEntry).filter(JournalEntry.id == res["journal_entry_id"]).first()
    assert je.organization_id == org.id
    assert "Approved Invoice" in je.description

    lines = session.query(JournalEntryLine).filter(JournalEntryLine.journal_entry_id == je.id).all()
    assert len(lines) == 2
    # Accounts receivable line
    ar_line = next(l for l in lines if l.account_code == "1100")
    assert ar_line.debit == Decimal("12000.00")
    assert ar_line.credit == Decimal("0.00")

    # Revenue line
    rev_line = next(l for l in lines if l.account_code == "4000")
    assert rev_line.debit == Decimal("0.00")
    assert rev_line.credit == Decimal("12000.00")
