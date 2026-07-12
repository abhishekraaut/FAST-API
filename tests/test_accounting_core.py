from decimal import Decimal

from app.domain.accounting.entities import JournalEntry, JournalEntryLine
from app.domain.accounting.rules import validate_journal_entry


def test_balanced_journal_entry_is_valid():
    entry = JournalEntry(
        description="Invoice issued",
        lines=[
            JournalEntryLine(account_code="1100", debit=Decimal("100.00")),
            JournalEntryLine(account_code="4000", credit=Decimal("100.00")),
        ],
    )

    validate_journal_entry(entry)


def test_unbalanced_journal_entry_is_rejected():
    entry = JournalEntry(
        description="Broken entry",
        lines=[
            JournalEntryLine(account_code="1100", debit=Decimal("100.00")),
            JournalEntryLine(account_code="4000", credit=Decimal("90.00")),
        ],
    )

    try:
        validate_journal_entry(entry)
    except ValueError as exc:
        assert "balanced" in str(exc).lower()
    else:
        raise AssertionError("Expected ValueError for unbalanced journal entry")
