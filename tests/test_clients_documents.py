from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.database.base import Base
from app.models.organization import Organization
from app.schemas.client import ClientCreate
from app.schemas.document import DocumentCreate
from app.services.client_service import ClientService
from app.services.document_service import DocumentService


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


def test_client_creation_is_scoped_to_organization(session: Session) -> None:
    org_a = Organization(name="Org A", slug="org-a", currency="INR")
    org_b = Organization(name="Org B", slug="org-b", currency="INR")
    session.add_all([org_a, org_b])
    session.commit()
    session.refresh(org_a)
    session.refresh(org_b)

    service = ClientService(session)
    service.create(
        ClientCreate(name="Acme Corp", email="acme@example.com", phone="123456", organization_id=org_a.id),
        organization_id=org_a.id,
    )

    result = service.list(organization_id=org_a.id, q="Acme")
    assert len(result) == 1

    other_result = service.list(organization_id=org_b.id, q="Acme")
    assert len(other_result) == 0


def test_document_upload_stores_file_and_tracks_status(session: Session) -> None:
    org = Organization(name="Org", slug="org", currency="INR")
    session.add(org)
    session.commit()
    session.refresh(org)

    with TemporaryDirectory() as tmpdir:
        storage_dir = Path(tmpdir)
        service = DocumentService(session, storage_dir=str(storage_dir))
        payload = DocumentCreate(document_type="invoice", description="Invoice upload")
        document = service.create_from_upload(
            organization_id=org.id,
            payload=payload,
            filename="invoice.pdf",
            content_type="application/pdf",
            file_bytes=b"%PDF-1.4\n% fake pdf",
        )

        assert document.status == "uploaded"
        assert document.storage_path is not None
        assert Path(document.storage_path).exists()
