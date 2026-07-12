from __future__ import annotations

USER_ROLES = ["owner", "admin", "accountant", "employee", "viewer"]
DOCUMENT_TYPES = ["invoice", "bill", "receipt", "bank_statement", "other"]
DOCUMENT_STATUSES = ["uploaded", "processing", "extracted", "needs_review", "confirmed", "failed"]
INVOICE_STATUSES = ["draft", "issued", "partially_paid", "paid", "overdue", "void"]
EXPENSE_STATUSES = ["draft", "pending_approval", "approved", "paid"]
PAYMENT_STATUSES = ["pending", "completed", "failed", "refunded"]
