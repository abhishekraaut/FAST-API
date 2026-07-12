# AI Accounting Backend

FastAPI backend for an AI-powered accounting SaaS with modular architecture, multi-tenant organization boundaries, document processing OCR/extraction, double-entry bookkeeping (INR/GST/TDS), and intent-based conversational accounting workflows.

## Current Implementation Status

| Phase | Status | Deliverable |
|-------|--------|-------------|
| Phase 1 — Requirement Analysis | Complete | Assumptions & scope defined |
| Phase 2 — System Design | Complete | [docs/PHASE_2_SYSTEM_DESIGN.md](docs/PHASE_2_SYSTEM_DESIGN.md) |
| Phase 3 — Database Design | Complete | [docs/PHASE_3_DATABASE_DESIGN.md](docs/PHASE_3_DATABASE_DESIGN.md) |
| Phase 4+ — Foundation & Modules | In Progress | Auth, accounting, and organization scaffolding implemented |

## What is implemented

- FastAPI application with health, auth, organization, accounting, client, vendor, document, account, and ledger routes
- SQLAlchemy base and startup DB initialization
- Pydantic-based auth, organization, client, vendor, document, account, and accounting schemas
- JWT and password hashing helpers
- Domain-level accounting validation using Decimal-based journal entry rules
- Local document storage and upload validation for MVP
- Core documentation for system design, database design, clients/documents workflow, and accounting foundation

## Run locally

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

## API Examples

### Health

```bash
curl http://localhost:8000/health
```

### Register user

```bash
curl -X POST http://localhost:8000/auth/register -H "Content-Type: application/json" -d '{"email":"user@example.com","full_name":"Test User","password":"123456"}'
```

### Create organization

```bash
curl -X POST http://localhost:8000/organizations -H "Content-Type: application/json" -d '{"name":"Acme Corp","slug":"acme-corp"}'
```

### Post a balanced journal entry

```bash
curl -X POST http://localhost:8000/accounting/journal-entries -H "Content-Type: application/json" -d '{"description":"Invoice issued","lines":[{"account_code":"1100","debit":100.00},{"account_code":"4000","credit":100.00}]}'
```

## Next steps

- Add Alembic migrations and real PostgreSQL support
- Implement full CRUD for documents, invoices, expenses, and payments
- Add JWT-protected multi-tenant middleware and RBAC enforcement
- Add AI provider abstraction and document processing pipeline

## License

Private — technical assignment project.
