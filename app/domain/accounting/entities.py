from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
from typing import List


@dataclass(slots=True)
class JournalEntryLine:
    account_code: str
    debit: Decimal = Decimal("0.00")
    credit: Decimal = Decimal("0.00")


@dataclass(slots=True)
class JournalEntry:
    description: str
    lines: List[JournalEntryLine] = field(default_factory=list)
