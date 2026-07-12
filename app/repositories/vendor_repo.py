from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.vendor import Vendor
from app.repositories.base import BaseRepository


class VendorRepository(BaseRepository[Vendor]):
    def __init__(self, session: Session) -> None:
        super().__init__(session, Vendor)

    def list_for_organization(self, organization_id: int, q: str | None = None) -> list[Vendor]:
        query = self.session.query(Vendor).filter(Vendor.organization_id == organization_id)
        if q:
            query = query.filter(Vendor.name.ilike(f"%{q}%"))
        return query.order_by(Vendor.name).all()

    def create(self, vendor: Vendor) -> Vendor:
        self.session.add(vendor)
        self.session.commit()
        self.session.refresh(vendor)
        return vendor

    def get_by_name_and_org(self, organization_id: int, name: str) -> Vendor | None:
        return self.session.query(Vendor).filter(Vendor.organization_id == organization_id, Vendor.name == name).first()
