from __future__ import annotations

from sqlalchemy.orm import Session

from app.core.exceptions import DuplicateResourceError
from app.models.account import Account
from app.repositories.account_repo import AccountRepository
from app.schemas.account import AccountCreate, AccountOut


class AccountService:
    def __init__(self, session: Session) -> None:
        self.repo = AccountRepository(session)

    def create(self, payload: AccountCreate, organization_id: int) -> AccountOut:
        if self.repo.get_by_code_and_org(organization_id, payload.code):
            raise DuplicateResourceError("Account code already exists")
        account = Account(organization_id=organization_id, code=payload.code, name=payload.name, account_type=payload.account_type.upper())
        saved = self.repo.create(account)
        return AccountOut.model_validate(saved)

    def list(self, organization_id: int) -> list[AccountOut]:
        accounts = self.repo.list_for_organization(organization_id)
        return [AccountOut.model_validate(account) for account in accounts]
