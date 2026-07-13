from __future__ import annotations

from sqlalchemy import ForeignKey, String, DECIMAL
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class BankAccount(Base):
    __tablename__ = "bank_accounts"

    id: Mapped[int] = mapped_column(primary_key=True)
    organization_id: Mapped[int] = mapped_column(ForeignKey("organizations.id"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    account_number: Mapped[str] = mapped_column(String(100), nullable=False)
    balance: Mapped[str] = mapped_column(String(50), default="0.00", nullable=False)


class BankTransaction(Base):
    __tablename__ = "bank_transactions"

    id: Mapped[int] = mapped_column(primary_key=True)
    organization_id: Mapped[int] = mapped_column(ForeignKey("organizations.id"), nullable=False, index=True)
    bank_account_id: Mapped[int] = mapped_column(ForeignKey("bank_accounts.id"), nullable=False, index=True)
    transaction_date: Mapped[str] = mapped_column(String(50), nullable=False)
    description: Mapped[str] = mapped_column(String(500), nullable=False)
    amount: Mapped[str] = mapped_column(String(50), nullable=False)  # positive for deposit, negative for withdrawal
    status: Mapped[str] = mapped_column(String(50), default="unmatched", nullable=False)  # "unmatched", "matched"
    matched_journal_entry_id: Mapped[int | None] = mapped_column(ForeignKey("journal_entries.id"), nullable=True)
