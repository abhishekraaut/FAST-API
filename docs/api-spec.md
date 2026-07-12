# API Specification

## Authentication
- POST /api/auth/register
  - body: email, password, full_name, company_name
  - returns: access_token, refresh_token, user
- POST /api/auth/login
  - body: email, password
  - returns: access_token, refresh_token, user
- POST /api/auth/refresh
  - body: refresh_token
- GET /api/auth/me

## Documents
- GET /api/documents?page=1&limit=20&status=processed
- POST /api/documents/upload
  - multipart/form-data with file
- GET /api/documents/{id}
- POST /api/documents/{id}/classify

## Invoices
- GET /api/invoices
- POST /api/invoices
- GET /api/invoices/{id}
- PATCH /api/invoices/{id}
- DELETE /api/invoices/{id}

## Expenses
- GET /api/expenses
- POST /api/expenses
- GET /api/expenses/{id}
- PATCH /api/expenses/{id}

## Ledger
- GET /api/ledger
- POST /api/ledger/entries

## Reports
- GET /api/reports/profit-loss
- GET /api/reports/cash-flow
- GET /api/reports/gst
- GET /api/reports/tds

## Chat
- POST /api/chat/query

## Tasks
- GET /api/tasks
- POST /api/tasks
- PATCH /api/tasks/{id}
