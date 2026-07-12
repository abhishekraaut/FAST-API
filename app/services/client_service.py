from __future__ import annotations

from sqlalchemy.orm import Session

from app.core.exceptions import DuplicateResourceError
from app.models.client import Client
from app.repositories.client_repo import ClientRepository
from app.schemas.client import ClientCreate, ClientOut


class ClientService:
    def __init__(self, session: Session) -> None:
        self.repo = ClientRepository(session)

    def create(self, payload: ClientCreate, organization_id: int) -> ClientOut:
        if self.repo.get_by_name_and_org(organization_id, payload.name):
            raise DuplicateResourceError("Client already exists")
        client = Client(
            organization_id=organization_id,
            name=payload.name,
            email=str(payload.email) if payload.email else None,
            phone=payload.phone,
        )
        saved = self.repo.create(client)
        return ClientOut.model_validate(saved)

    def list(self, organization_id: int, q: str | None = None) -> list[ClientOut]:
        clients = self.repo.list_for_organization(organization_id, q=q)
        return [ClientOut.model_validate(client) for client in clients]
