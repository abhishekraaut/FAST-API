# PHASE 5 — Accounting Foundation

## Implemented scope
- Organization-scoped chart of accounts
- Journal entry posting with Decimal-based lines
- Balanced-entry validation using the existing domain rules
- API routes for accounts and ledger posting
- Repository and service layers for account and journal entry use cases

## Notes
- Financial values remain Decimal-based and are stored using SQL DECIMAL-compatible values in the ORM models.
- Posted entries are treated as immutable in the current MVP implementation.
- Corrections should be implemented as reversal/adjustment entries in a later phase.
