from __future__ import annotations

from sqlalchemy.orm import Session

from app.core.exceptions import DuplicateResourceError
from app.models.vendor import Vendor
from app.repositories.vendor_repo import VendorRepository
from app.schemas.vendor import VendorCreate, VendorOut


class VendorService:
    def __init__(self, session: Session) -> None:
        self.repo = VendorRepository(session)

    def create(self, payload: VendorCreate, organization_id: int) -> VendorOut:
        if self.repo.get_by_name_and_org(organization_id, payload.name):
            raise DuplicateResourceError("Vendor already exists")
        vendor = Vendor(
            organization_id=organization_id,
            name=payload.name,
            email=str(payload.email) if payload.email else None,
            phone=payload.phone,
            tax_number=payload.tax_number,
        )
        saved = self.repo.create(vendor)
        return VendorOut.model_validate(saved)

    def list(self, organization_id: int, q: str | None = None) -> list[VendorOut]:
        vendors = self.repo.list_for_organization(organization_id, q=q)
        return [VendorOut.model_validate(vendor) for vendor in vendors]
