from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.account import Account
from app.repositories.base import BaseRepository


class AccountRepository(BaseRepository[Account]):
    def __init__(self, session: Session) -> None:
        super().__init__(session, Account)

    def create(self, account: Account) -> Account:
        self.session.add(account)
        self.session.commit()
        self.session.refresh(account)
        return account

    def list_for_organization(self, organization_id: int) -> list[Account]:
        return self.session.query(Account).filter(Account.organization_id == organization_id).order_by(Account.code).all()

    def get_by_code_and_org(self, organization_id: int, code: str) -> Account | None:
        return self.session.query(Account).filter(Account.organization_id == organization_id, Account.code == code).first()
