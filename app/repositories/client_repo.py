from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.client import Client
from app.repositories.base import BaseRepository


class ClientRepository(BaseRepository[Client]):
    def __init__(self, session: Session) -> None:
        super().__init__(session, Client)

    def list_for_organization(self, organization_id: int, q: str | None = None) -> list[Client]:
        query = self.session.query(Client).filter(Client.organization_id == organization_id)
        if q:
            query = query.filter(Client.name.ilike(f"%{q}%"))
        return query.order_by(Client.name).all()

    def create(self, client: Client) -> Client:
        self.session.add(client)
        self.session.commit()
        self.session.refresh(client)
        return client

    def get_by_name_and_org(self, organization_id: int, name: str) -> Client | None:
        return self.session.query(Client).filter(Client.organization_id == organization_id, Client.name == name).first()
