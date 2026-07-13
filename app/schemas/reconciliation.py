from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class BankAccountCreate(BaseModel):
    name: str
    account_number: str
    balance: str = "0.00"


class BankAccountOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    organization_id: int
    name: str
    account_number: str
    balance: str


class BankTransactionCreate(BaseModel):
    transaction_date: str
    description: str
    amount: str


class BankTransactionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    organization_id: int
    bank_account_id: int
    transaction_date: str
    description: str
    amount: str
    status: str
    matched_journal_entry_id: int | None = None


class ReconciliationMatchRequest(BaseModel):
    journal_entry_id: int
