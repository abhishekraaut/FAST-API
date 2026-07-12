from __future__ import annotations

from sqlalchemy.orm import Session

from app.core.exceptions import DuplicateResourceError
from app.models.organization import Organization
from app.repositories.organization_repo import OrganizationRepository
from app.schemas.organization import OrganizationCreate, OrganizationOut


class OrganizationService:
    def __init__(self, session: Session) -> None:
        self.repo = OrganizationRepository(session)

    def create(self, payload: OrganizationCreate) -> OrganizationOut:
        if self.repo.get_by_slug(payload.slug):
            raise DuplicateResourceError("Organization slug already exists")
        organization = Organization(name=payload.name, slug=payload.slug, currency=payload.currency)
        saved = self.repo.create(organization)
        return OrganizationOut(id=saved.id, name=saved.name, slug=saved.slug, currency=saved.currency)
