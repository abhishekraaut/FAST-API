# PHASE 3 — Database Design

## 1. Core Entities

- Organization
- User
- Membership
- Document
- DocumentExtraction
- Account
- JournalEntry
- JournalEntryLine
- Invoice
- InvoiceItem
- Expense
- Payment
- BankAccount
- BankTransaction
- Reconciliation
- TaxRecord
- ComplianceFiling
- Task
- Reminder
- Conversation
- Message
- AuditLog

## 2. Multi-Tenancy Strategy

All tenant-scoped tables should include an organization_id foreign key and every query must filter by the authenticated organization context.

## 3. Important Design Decisions

- Use UUIDs for public identifiers where possible.
- Use DECIMAL for financial values rather than float.
- Keep journal entries immutable after posting.
- Use soft-delete where business history must be preserved.
- Store audit timestamps with created_at/updated_at.

## 4. ER Diagram

```mermaid
erDiagram
    ORGANIZATION ||--o{ MEMBERSHIP : has
    USER ||--o{ MEMBERSHIP : belongs_to
    ORGANIZATION ||--o{ DOCUMENT : owns
    ORGANIZATION ||--o{ ACCOUNT : owns
    ACCOUNT ||--o{ JOURNAL_ENTRY_LINE : posts_to
    JOURNAL_ENTRY ||--o{ JOURNAL_ENTRY_LINE : contains
    ORGANIZATION ||--o{ INVOICE : issues
    INVOICE ||--o{ INVOICE_ITEM : contains
    INVOICE ||--o{ PAYMENT : receives
    ORGANIZATION ||--o{ EXPENSE : tracks
    EXPENSE ||--o{ PAYMENT : settles
```
