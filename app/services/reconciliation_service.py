from __future__ import annotations

from decimal import Decimal
from sqlalchemy.orm import Session

from app.core.exceptions import ResourceNotFoundError, ValidationError
from app.models.reconciliation import BankAccount, BankTransaction
from app.models.journal_entry import JournalEntry
from app.models.journal_entry_line import JournalEntryLine
from app.schemas.reconciliation import BankAccountCreate, BankTransactionCreate


class ReconciliationService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create_bank_account(self, organization_id: int, payload: BankAccountCreate) -> BankAccount:
        account = BankAccount(
            organization_id=organization_id,
            name=payload.name,
            account_number=payload.account_number,
            balance=payload.balance,
        )
        self.db.add(account)
        self.db.commit()
        self.db.refresh(account)
        return account

    def list_bank_accounts(self, organization_id: int) -> list[BankAccount]:
        return self.db.query(BankAccount).filter(BankAccount.organization_id == organization_id).all()

    def get_bank_account(self, bank_account_id: int, organization_id: int) -> BankAccount:
        acc = self.db.query(BankAccount).filter(BankAccount.id == bank_account_id, BankAccount.organization_id == organization_id).first()
        if not acc:
            raise ResourceNotFoundError(f"Bank Account with ID {bank_account_id} not found")
        return acc

    def create_bank_transaction(
        self, organization_id: int, bank_account_id: int, payload: BankTransactionCreate
    ) -> BankTransaction:
        # Verify bank account exists
        self.get_bank_account(bank_account_id, organization_id)

        tx = BankTransaction(
            organization_id=organization_id,
            bank_account_id=bank_account_id,
            transaction_date=payload.transaction_date,
            description=payload.description,
            amount=payload.amount,
            status="unmatched",
        )
        self.db.add(tx)
        self.db.commit()
        self.db.refresh(tx)
        return tx

    def list_transactions(self, organization_id: int, bank_account_id: int, status: str | None = None) -> list[BankTransaction]:
        self.get_bank_account(bank_account_id, organization_id)
        query = self.db.query(BankTransaction).filter(
            BankTransaction.organization_id == organization_id,
            BankTransaction.bank_account_id == bank_account_id
        )
        if status:
            query = query.filter(BankTransaction.status == status)
        return query.order_by(BankTransaction.id.desc()).all()

    def manual_match(self, organization_id: int, transaction_id: int, journal_entry_id: int) -> BankTransaction:
        tx = self.db.query(BankTransaction).filter(
            BankTransaction.id == transaction_id,
            BankTransaction.organization_id == organization_id
        ).first()
        if not tx:
            raise ResourceNotFoundError(f"Bank Transaction with ID {transaction_id} not found")

        je = self.db.query(JournalEntry).filter(
            JournalEntry.id == journal_entry_id,
            JournalEntry.organization_id == organization_id
        ).first()
        if not je:
            raise ResourceNotFoundError(f"Journal Entry with ID {journal_entry_id} not found")

        tx.status = "matched"
        tx.matched_journal_entry_id = je.id
        self.db.add(tx)
        self.db.commit()
        self.db.refresh(tx)
        return tx

    def auto_reconcile(self, organization_id: int, bank_account_id: int) -> int:
        """
        Auto reconciles bank transactions with posted ledger journal entries.
        Matches by amount (absolute value equal to debit or credit in posted lines) and date.
        """
        unmatched_txs = self.list_transactions(organization_id, bank_account_id, status="unmatched")
        journal_entries = self.db.query(JournalEntry).filter(
            JournalEntry.organization_id == organization_id,
            JournalEntry.status == "posted"
        ).all()

        match_count = 0
        for tx in unmatched_txs:
            tx_amount = Decimal(str(tx.amount))
            abs_amount = abs(tx_amount)

            # Look for a matching posted journal entry line
            matched_je = None
            for je in journal_entries:
                # Basic amount match checking on lines
                lines = self.db.query(JournalEntryLine).filter(JournalEntryLine.journal_entry_id == je.id).all()
                for line in lines:
                    line_amt = Decimal(str(line.debit)) if line.debit != Decimal("0.00") else Decimal(str(line.credit))
                    if line_amt == abs_amount:
                        # Ensure this JE is not already reconciled
                        already_matched = self.db.query(BankTransaction).filter(
                            BankTransaction.matched_journal_entry_id == je.id
                        ).first()
                        if not already_matched:
                            matched_je = je
                            break
                if matched_je:
                    break

            if matched_je:
                tx.status = "matched"
                tx.matched_journal_entry_id = matched_je.id
                self.db.add(tx)
                match_count += 1

        if match_count > 0:
            self.db.commit()

        return match_count
