from __future__ import annotations

from decimal import Decimal

from app.domain.accounting.entities import JournalEntry


def validate_journal_entry(entry: JournalEntry) -> None:
    debit_total = sum((line.debit for line in entry.lines), Decimal("0.00"))
    credit_total = sum((line.credit for line in entry.lines), Decimal("0.00"))

    if debit_total != credit_total:
        raise ValueError(
            f"Journal entry is not balanced: debits={debit_total} credits={credit_total}"
        )
