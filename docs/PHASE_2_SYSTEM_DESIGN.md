# PHASE 2 — System Design

**Project:** AI Accounting SaaS Backend  
**Stack:** FastAPI · SQLAlchemy 2.x · MySQL 8 · Alembic · Pydantic v2  
**Jurisdiction:** India (INR, GST, TDS)  
**Status:** Design complete — no application code yet  
**Last updated:** July 2026

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [High-Level Architecture](#2-high-level-architecture)
3. [Folder Structure](#3-folder-structure)
4. [Module Boundaries & Responsibilities](#4-module-boundaries--responsibilities)
5. [Layered Architecture (Clean Architecture)](#5-layered-architecture-clean-architecture)
6. [Request Flow — Typical REST API](#6-request-flow--typical-rest-api)
7. [Document Processing Flow](#7-document-processing-flow)
8. [AI Orchestration Flow](#8-ai-orchestration-flow)
9. [Accounting Transaction Flow](#9-accounting-transaction-flow)
10. [Conversational Command Flow](#10-conversational-command-flow)
11. [Multi-Tenant Isolation Strategy](#11-multi-tenant-isolation-strategy)
12. [Provider Abstractions](#12-provider-abstractions)
13. [Background Processing Strategy](#13-background-processing-strategy)
14. [Data Model Overview](#14-data-model-overview)
15. [Security & RBAC](#15-security--rbac)
16. [Sync vs Async Database Strategy](#16-sync-vs-async-database-strategy)
17. [Future Module Extraction Path](#17-future-module-extraction-path)
18. [Architectural Decision Records (ADRs)](#18-architectural-decision-records-adrs)
19. [Interview Defense Guide](#19-interview-defense-guide)
20. [Optional Production Enhancements](#20-optional-production-enhancements)

---

## 1. Executive Summary

This backend is a **modular monolith** implementing **Clean Architecture** for an AI-powered accounting SaaS. It serves a separate frontend and handles:

- Multi-tenant organization management with JWT + RBAC
- Document upload, OCR, and AI-assisted field extraction
- Double-entry bookkeeping with Decimal precision
- India-specific compliance (GST, TDS)
- Intent-based conversational commands (never direct LLM → DB)

The MVP uses **Groq** for AI, **Tesseract** for OCR, **local filesystem** for storage, and **FastAPI BackgroundTasks** for async work. Each external dependency is hidden behind a provider interface so production can swap to OpenAI, AWS Textract, S3, and Celery without rewriting business logic.

---

## 2. High-Level Architecture

### 2.1 System Context Diagram

```mermaid
C4Context
    title System Context — AI Accounting SaaS

    Person(user, "Accountant / Business Owner", "Uploads invoices, reviews entries, chats with AI")
    Person(admin, "Org Admin", "Manages users, roles, org settings")

    System(backend, "AI Accounting Backend", "FastAPI modular monolith")
    System_Ext(frontend, "React Frontend", "Separate SPA — not in this repo")
    System_Ext(groq, "Groq API", "LLM inference")
    System_Ext(tesseract, "Tesseract OCR", "Local OCR engine")
    System_Ext(mysql, "MySQL 8", "Primary datastore")

    Rel(user, frontend, "Uses")
    Rel(admin, frontend, "Administers")
    Rel(frontend, backend, "HTTPS / REST + JWT")
    Rel(backend, mysql, "SQLAlchemy ORM")
    Rel(backend, groq, "Structured prompts")
    Rel(backend, tesseract, "OCR subprocess")
```

### 2.2 Container Diagram (Internal Modules)

```mermaid
flowchart TB
    subgraph Client["External"]
        FE[Frontend SPA]
    end

    subgraph API["API Layer"]
        R1[Auth Router]
        R2[Documents Router]
        R3[Accounting Router]
        R4[Chat Router]
        R5[Reports Router]
        MW[Middleware<br/>CORS · Tenant · Auth · Logging]
    end

    subgraph Services["Service Layer"]
        S1[AuthService]
        S2[DocumentService]
        S3[AccountingService]
        S4[ChatOrchestrator]
        S5[ReportService]
        S6[ReconciliationService]
        S7[ComplianceService]
    end

    subgraph Domain["Domain Layer"]
        D1[JournalEntry · LedgerAccount]
        D2[Invoice · Payment · GST]
        D3[Reconciliation Rules]
        D4[Intent · Command]
    end

    subgraph Infra["Infrastructure"]
        REPO[Repositories]
        AI[AIProvider → Groq]
        OCR[OCRProvider → Tesseract]
        STOR[StorageProvider → Local FS]
        DB[(MySQL 8)]
        BG[BackgroundTasks]
    end

    FE --> MW --> R1 & R2 & R3 & R4 & R5
    R1 --> S1
    R2 --> S2
    R3 --> S3
    R4 --> S4
    R5 --> S5
    S2 --> OCR & STOR & AI
    S3 --> D1 & D2
    S4 --> AI & S3
    S1 & S2 & S3 & S4 & S5 & S6 & S7 --> REPO --> DB
    S2 --> BG
```

### 2.3 Dependency Rule (Clean Architecture)

Dependencies point **inward only**. Outer layers depend on inner abstractions — never the reverse.

```mermaid
flowchart LR
    subgraph Outer["Outer (Frameworks & Drivers)"]
        API[API / Routers]
        INFRA[Infrastructure<br/>SQLAlchemy · Groq · Tesseract · FS]
    end

    subgraph Middle["Application"]
        SVC[Services / Use Cases]
        REPO_IF[Repository Interfaces]
    end

    subgraph Inner["Domain"]
        ENT[Entities & Value Objects]
        RULES[Business Rules]
    end

    API --> SVC
    SVC --> REPO_IF
    SVC --> ENT
    SVC --> RULES
    INFRA -.->|implements| REPO_IF
    INFRA --> ENT
```

---

## 3. Folder Structure

Finalized layout for Phase 3+ implementation:

```
app/
├── main.py                          # App factory, lifespan, router registration
├── api/
│   └── v1/
│       ├── routers/
│       │   ├── auth.py
│       │   ├── organizations.py
│       │   ├── users.py
│       │   ├── documents.py
│       │   ├── accounting.py        # journal entries, accounts, invoices
│       │   ├── chat.py
│       │   ├── reports.py
│       │   └── health.py
│       └── deps.py                  # get_db, get_current_user, get_org_context
├── core/
│   ├── config.py                    # pydantic-settings
│   ├── security.py                  # JWT, password hashing
│   ├── exceptions.py                # domain + HTTP exception mapping
│   ├── logging.py
│   └── constants.py                 # roles, permissions, enums
├── database/
│   ├── session.py                   # engine, SessionLocal, get_db
│   └── base.py                      # DeclarativeBase
├── models/                          # SQLAlchemy ORM models (persistence)
│   ├── organization.py
│   ├── user.py
│   ├── document.py
│   ├── accounting.py
│   └── chat.py
├── schemas/                         # Pydantic v2 DTOs (request/response)
│   ├── auth.py
│   ├── organization.py
│   ├── document.py
│   ├── accounting.py
│   └── chat.py
├── repositories/                    # Data access — org-scoped queries
│   ├── base.py
│   ├── organization_repo.py
│   ├── user_repo.py
│   ├── document_repo.py
│   ├── accounting_repo.py
│   └── chat_repo.py
├── services/                        # Application / use-case orchestration
│   ├── auth_service.py
│   ├── organization_service.py
│   ├── document_service.py
│   ├── accounting_service.py
│   ├── chat_service.py
│   └── report_service.py
├── domain/                          # Pure business logic — no FastAPI/SQLAlchemy imports
│   ├── accounting/
│   │   ├── entities.py              # JournalEntry, LedgerLine, Money
│   │   ├── rules.py                 # double-entry validation, balance checks
│   │   └── chart_of_accounts.py
│   ├── reconciliation/
│   │   └── matcher.py
│   └── compliance/
│       ├── gst.py                   # GST rate / HSN helpers
│       └── tds.py
├── ai/
│   ├── providers/
│   │   ├── base.py                  # AIProvider ABC
│   │   └── groq_provider.py
│   ├── prompts/
│   │   ├── extraction.py
│   │   ├── classification.py
│   │   └── intent.py
│   ├── schemas/                     # Pydantic models for LLM structured output
│   │   ├── extraction_result.py
│   │   └── intent_result.py
│   └── orchestrator/
│       ├── extraction_orchestrator.py
│       └── chat_orchestrator.py
├── document_processing/
│   ├── storage/
│   │   ├── base.py                  # StorageProvider ABC
│   │   └── local_storage.py
│   ├── ocr/
│   │   ├── base.py                  # OCRProvider ABC
│   │   └── tesseract_provider.py
│   └── extraction/
│       └── pipeline.py              # OCR → AI → validated DTO
├── tasks/
│   ├── document_tasks.py            # BackgroundTasks wrappers (MVP)
│   └── celery_tasks.py              # stub / migration path
├── middleware/
│   ├── tenant.py                    # org_id extraction & validation
│   └── request_id.py
└── utils/
    ├── decimal_utils.py
    └── date_utils.py

tests/
├── unit/
├── integration/
└── conftest.py

alembic/
├── versions/
└── env.py

scripts/
├── seed_chart_of_accounts.py
└── create_admin.py

docs/
├── PHASE_2_SYSTEM_DESIGN.md         # this document
└── (future ADR index, API spec)
```

---

## 4. Module Boundaries & Responsibilities

| Module | Owns | Does NOT Own | Key Interfaces |
|--------|------|--------------|----------------|
| **core** | Config, JWT, global exceptions, logging | Business rules | `Settings`, `create_access_token()` |
| **api/v1** | HTTP routing, request validation, response serialization, status codes | DB queries, AI calls | FastAPI routers + `deps.py` |
| **schemas** | Pydantic DTOs for API I/O | Persistence logic | `*Create`, `*Update`, `*Response` |
| **services** | Use-case orchestration, transaction boundaries, calling repos + providers | HTTP concerns, raw SQL | `AccountingService.post_journal_entry()` |
| **repositories** | CRUD, org-scoped queries, SQLAlchemy mapping | Business validation | `JournalEntryRepository.create()` |
| **domain** | Pure accounting rules, Money/Decimal math, GST/TDS logic | Any I/O | `JournalEntry.validate_balanced()` |
| **models** | SQLAlchemy table definitions | API shapes | ORM classes |
| **ai/** | LLM prompts, structured output parsing, provider swap | DB writes | `AIProvider.complete_structured()` |
| **document_processing/** | File storage, OCR, extraction pipeline | Journal posting | `StorageProvider`, `OCRProvider` |
| **tasks/** | Deferred work scheduling | Business logic duplication | `process_document_task()` |
| **middleware** | Cross-cutting: tenant context, request ID | Authorization decisions | `TenantMiddleware` |

### Module Interaction Rules

1. **Routers** call exactly one **Service** method per endpoint (thin controllers).
2. **Services** coordinate **Repositories**, **Domain** rules, and **Providers**.
3. **Repositories** never call Services or AI.
4. **Domain** has zero imports from `app.models`, `fastapi`, or provider packages.
5. **AI Orchestrator** returns validated Pydantic DTOs; Services decide whether to persist.

---

## 5. Layered Architecture (Clean Architecture)

```mermaid
flowchart TB
    subgraph L1["Layer 1 — API / Router"]
        direction LR
        A1[Parse HTTP]
        A2[Auth via deps]
        A3[Return DTO]
    end

    subgraph L2["Layer 2 — Schema / DTO"]
        direction LR
        B1[Request validation]
        B2[Response serialization]
    end

    subgraph L3["Layer 3 — Service"]
        direction LR
        C1[Use-case logic]
        C2[Transaction boundary]
        C3[Call domain rules]
    end

    subgraph L4["Layer 4 — Repository"]
        direction LR
        D1[Org-scoped queries]
        D2[ORM ↔ Entity mapping]
    end

    subgraph L5["Layer 5 — Domain"]
        direction LR
        E1[Entities]
        E2[Invariant enforcement]
    end

    subgraph L6["Layer 6 — Infrastructure"]
        direction LR
        F1[MySQL]
        F2[Groq]
        F3[Tesseract]
        F4[Local FS]
    end

    L1 --> L2 --> L3 --> L4 --> L5
    L3 --> L5
    L4 --> L6
    L3 --> L6
```

---

## 6. Request Flow — Typical REST API

Example: `POST /api/v1/accounting/journal-entries` — create a balanced journal entry.

```mermaid
sequenceDiagram
    autonumber
    participant FE as Frontend
    participant MW as Middleware
    participant RT as accounting.router
    participant DEP as deps.py
    participant SCH as schemas.accounting
    participant SVC as AccountingService
    participant DOM as domain.accounting
    participant REPO as JournalEntryRepository
    participant DB as MySQL

    FE->>MW: POST /journal-entries<br/>Authorization: Bearer JWT<br/>X-Org-Id: {org_id}
    MW->>MW: Attach request_id, parse org header
    MW->>RT: Forward request
    RT->>DEP: get_current_user(), get_db(), get_org_context()
    DEP->>DEP: Decode JWT → user_id, roles
    DEP->>DEP: Verify user ∈ org, check permission ACCOUNTING_WRITE
    RT->>SCH: JournalEntryCreate (Pydantic validation)
    SCH-->>RT: Validated DTO (Decimal amounts, ≥2 lines)
    RT->>SVC: create_journal_entry(org_id, dto, user_id)
    SVC->>DOM: JournalEntry.from_dto(dto)
    DOM->>DOM: validate_balanced() — debits == credits
    DOM->>DOM: validate_accounts_active()
    alt Validation fails
        DOM-->>SVC: DomainError
        SVC-->>RT: raise UnbalancedEntryError
        RT-->>FE: 422 Unprocessable Entity
    end
    SVC->>REPO: create(entry, org_id)
    REPO->>DB: BEGIN; INSERT journal_entries + lines; COMMIT
    DB-->>REPO: Persisted row
    REPO-->>SVC: Domain entity
    SVC-->>RT: JournalEntryResponse
    RT-->>FE: 201 Created
```

### Error Handling Path

| Layer | Exception Type | HTTP Mapping |
|-------|---------------|--------------|
| Pydantic | `ValidationError` | 422 with field details |
| Domain | `UnbalancedEntryError` | 422 |
| Service | `NotFoundError`, `ForbiddenError` | 404, 403 |
| Repository | `IntegrityError` | 409 Conflict |
| Auth | `UnauthorizedError` | 401 |

All exceptions funnel through `core/exceptions.py` registered on the FastAPI app.

---

## 7. Document Processing Flow

End-to-end: user uploads a PDF invoice → OCR → AI extraction → human review → optional auto-draft journal entry.

```mermaid
flowchart TB
    subgraph Upload["Phase A — Synchronous (< 2s)"]
        U1[POST /documents/upload<br/>multipart/form-data]
        U2[DocumentService.create_upload]
        U3[StorageProvider.save<br/>org_id/doc_id/file.pdf]
        U4[DocumentRepository.insert<br/>status=PENDING]
        U5[BackgroundTasks.add_task<br/>process_document]
        U6[202/201 Response<br/>document_id + status]
    end

    subgraph Background["Phase B — Background Task"]
        B1[Load document record]
        B2[StorageProvider.read file]
        B3[OCRProvider.extract_text]
        B4[ExtractionOrchestrator]
        B5[AIProvider structured extraction]
        B6[Validate ExtractionResult schema]
        B7[Store raw OCR + extracted JSON]
        B8[Update status=EXTRACTED or FAILED]
    end

    subgraph Review["Phase C — Human in the Loop"]
        R1[GET /documents/{id}]
        R2[User edits extracted fields]
        R3[PATCH /documents/{id}/extraction]
        R4[POST /documents/{id}/approve]
    end

    subgraph Posting["Phase D — Optional Auto-Entry"]
        P1[DocumentService.create_draft_entry]
        P2[AccountingService.create_from_invoice]
        P3[Journal entry status=DRAFT]
    end

    U1 --> U2 --> U3 --> U4 --> U5 --> U6
    U5 -.-> B1 --> B2 --> B3 --> B4 --> B5 --> B6 --> B7 --> B8
    B8 --> R1 --> R2 --> R3 --> R4
    R4 --> P1 --> P2 --> P3
```

```mermaid
sequenceDiagram
    participant User
    participant API
    participant DocSvc as DocumentService
    participant Storage as StorageProvider
    participant BG as BackgroundTasks
    participant OCR as OCRProvider
    participant AI as ExtractionOrchestrator
    participant DB as MySQL

    User->>API: Upload invoice PDF
    API->>DocSvc: create_upload(file, org_id)
    DocSvc->>Storage: save(org_id, uuid, bytes)
    DocSvc->>DB: INSERT document (PENDING)
    DocSvc->>BG: schedule process_document(doc_id)
    API-->>User: { id, status: "PENDING" }

    BG->>DocSvc: process_document(doc_id)
    DocSvc->>Storage: read(path)
    DocSvc->>OCR: extract_text(bytes)
    OCR-->>DocSvc: raw_text
    DocSvc->>AI: extract(raw_text, doc_type=INVOICE)
    AI-->>DocSvc: ExtractionResult (validated)
    DocSvc->>DB: UPDATE document (EXTRACTED, ocr_text, extracted_json)
```

### Document Status State Machine

```mermaid
stateDiagram-v2
    [*] --> PENDING: Upload received
    PENDING --> PROCESSING: Background task starts
    PROCESSING --> EXTRACTED: OCR + AI success
    PROCESSING --> FAILED: OCR/AI/validation error
    EXTRACTED --> REVIEWED: User confirms/edits
    REVIEWED --> POSTED: Draft journal created
    REVIEWED --> ARCHIVED: Discarded
    FAILED --> PENDING: Retry
    POSTED --> [*]
    ARCHIVED --> [*]
```

---

## 8. AI Orchestration Flow

**Core principle:** The LLM is a **proposal engine**, not an executor. It returns structured JSON validated by Pydantic; Services apply domain rules before any DB write.

```mermaid
flowchart LR
    subgraph Input
        I1[OCR text / user message]
        I2[Context:<br/>org chart of accounts,<br/>recent entries,<br/>doc metadata]
    end

    subgraph Orchestrator
        O1[Select prompt template]
        O2[Build messages]
        O3[AIProvider.complete_structured]
        O4[Pydantic parse + repair retry]
        O5[Confidence scoring]
    end

    subgraph Output
        OUT1[ExtractionResult]
        OUT2[IntentResult]
        OUT3[Never raw SQL]
    end

    subgraph Guardrails
        G1[JSON schema enforcement]
        G2[Enum validation for accounts]
        G3[Decimal parsing — no floats]
        G4[Max token / timeout limits]
        G5[Audit log: prompt hash + response]
    end

    I1 --> O1
    I2 --> O2 --> O3 --> O4 --> O5
    O4 --> G1 & G2 & G3
    O3 --> G4 & G5
    O5 --> OUT1 & OUT2
```

### Extraction Orchestrator

```mermaid
sequenceDiagram
    participant SVC as DocumentService
    participant ORC as ExtractionOrchestrator
    participant PRM as prompts.extraction
    participant AI as GroqProvider
    participant SCH as ExtractionResult

    SVC->>ORC: extract(ocr_text, doc_type)
    ORC->>PRM: build_prompt(text, doc_type, gst_fields=true)
    ORC->>AI: complete_structured(messages, schema=ExtractionResult)
    AI-->>ORC: JSON string
    ORC->>SCH: model_validate(json)
    alt Parse failure (1 retry)
        ORC->>AI: repair prompt with error details
        AI-->>ORC: corrected JSON
        ORC->>SCH: model_validate(json)
    end
    SCH-->>ORC: Validated ExtractionResult
    ORC-->>SVC: result + confidence
    Note over SVC: Service stores result;<br/>does NOT auto-post without review flag
```

### AI Provider Interface

```python
# Conceptual — not implemented yet
class AIProvider(ABC):
    async def complete_structured(
        self,
        messages: list[Message],
        response_model: type[BaseModel],
        temperature: float = 0.0,
    ) -> BaseModel: ...

    async def complete_text(
        self,
        messages: list[Message],
    ) -> str: ...
```

MVP implementation: `GroqProvider` using Groq's chat completions with `response_format={"type": "json_object"}` and server-side Pydantic validation.

---

## 9. Accounting Transaction Flow

Double-entry bookkeeping: every transaction has ≥2 lines; total debits == total credits; amounts use `Decimal`.

```mermaid
flowchart TB
    subgraph Sources
        SRC1[Manual API entry]
        SRC2[Approved document]
        SRC3[Chat command — intent CREATE_ENTRY]
    end

    subgraph Validation["Domain Validation"]
        V1[≥ 2 lines]
        V2[Each line: debit XOR credit > 0]
        V3[Sum debits == sum credits]
        V4[Accounts belong to org]
        V5[Period not locked]
        V6[GST/TDS fields if applicable]
    end

    subgraph Persistence
        P1[Insert journal_entry header]
        P2[Insert journal_lines]
        P3[Update account balances — materialized or computed]
        P4[Insert audit_log]
    end

    SRC1 & SRC2 & SRC3 --> V1 --> V2 --> V3 --> V4 --> V5 --> V6
    V6 --> P1 --> P2 --> P3 --> P4
```

```mermaid
sequenceDiagram
    participant SVC as AccountingService
    participant DOM as domain.accounting
    participant COA as chart_of_accounts
    participant GST as compliance.gst
    participant REPO as AccountingRepository
    participant DB as MySQL

    SVC->>DOM: build JournalEntry from source
    DOM->>COA: resolve_account_codes(org_id, lines)
    DOM->>DOM: validate_balanced()
    DOM->>GST: apply_gst_lines(invoice_data)
    GST-->>DOM: additional tax lines (CGST/SGST/IGST)
    SVC->>REPO: save_entry(entry, org_id)
    REPO->>DB: BEGIN
    REPO->>DB: INSERT journal_entries
    REPO->>DB: INSERT journal_lines (Decimal columns)
    REPO->>DB: INSERT audit_logs
    REPO->>DB: COMMIT
    REPO-->>SVC: persisted entry
```

### Double-Entry Example (Purchase Invoice with GST)

| Account | Debit (INR) | Credit (INR) |
|---------|-------------|--------------|
| Office Expenses | 10,000.00 | |
| Input CGST | 900.00 | |
| Input SGST | 900.00 | |
| Accounts Payable | | 11,800.00 |
| **Totals** | **11,800.00** | **11,800.00** |

All amounts stored as `DECIMAL(19,4)` in MySQL; Python side uses `decimal.Decimal` exclusively — **never `float`**.

---

## 10. Conversational Command Flow

**Intent-based architecture:** Chat messages are classified into intents; each intent maps to a ** predefined Service method** — the LLM never generates or executes SQL.

```mermaid
flowchart TB
    subgraph Chat["POST /api/v1/chat/message"]
        C1[User: Show me last month's expenses]
        C2[ChatOrchestrator.handle]
    end

    subgraph Intent["Intent Classification"]
        I1[AIProvider → IntentResult]
        I2[intent: QUERY_EXPENSES]
        I3[entities: period=2026-06]
        I4[confidence: 0.92]
    end

    subgraph Routing["Intent Router — deterministic Python"]
        R1{intent type?}
        R2[ReportService.get_expenses]
        R3[AccountingService.create_entry]
        R4[DocumentService.search]
        R5[Clarification response]
    end

    subgraph Response
        RESP1[Structured data from Service]
        RESP2[AIProvider.format_response — natural language]
        RESP3[ChatResponse with citations]
    end

    C1 --> C2 --> I1 --> I2 & I3 & I4
    I2 --> R1
    R1 -->|QUERY_*| R2
    R1 -->|CREATE_ENTRY| R3
    R1 -->|SEARCH_DOCS| R4
    R1 -->|low confidence| R5
    R2 & R3 & R4 --> RESP1 --> RESP2 --> RESP3
```

```mermaid
sequenceDiagram
    participant User
    participant ChatSvc as ChatService
    participant ORC as ChatOrchestrator
    participant AI as GroqProvider
    participant Router as IntentRouter
    participant AcctSvc as AccountingService
    participant DB as MySQL

    User->>ChatSvc: "Create expense entry ₹5000 for office rent"
    ChatSvc->>ORC: handle(message, org_context, history)
    ORC->>AI: classify intent (IntentResult schema)
    AI-->>ORC: { intent: CREATE_ENTRY, entities: {...}, confidence: 0.88 }
    ORC->>Router: dispatch(intent, entities)

    alt confidence < 0.7
        Router-->>User: "Did you mean create an expense entry for ₹5000?"
    end

    Router->>AcctSvc: create_journal_entry(draft_dto)
    Note over AcctSvc: Same domain validation<br/>as REST API path
    AcctSvc->>DB: INSERT (if user confirmed or auto-confirm enabled)
    AcctSvc-->>ORC: entry summary
    ORC->>AI: format_response(data, tone=professional)
    AI-->>User: "Created draft entry #JE-1042 for Office Rent ₹5,000..."
```

### Supported MVP Intents

| Intent | Service Action | Mutates DB? |
|--------|---------------|-------------|
| `QUERY_BALANCE` | ReportService | Read-only |
| `QUERY_EXPENSES` | ReportService | Read-only |
| `SEARCH_DOCUMENTS` | DocumentService | Read-only |
| `CREATE_ENTRY` | AccountingService | Yes — after confirmation |
| `EXPLAIN_ENTRY` | AccountingService + AI format | Read-only |
| `UNKNOWN` | Return clarification | No |

### Hallucination Controls (Chat + Extraction)

| Control | Mechanism |
|---------|-----------|
| Structured output | Pydantic models with strict types |
| Intent whitelist | Router only handles known enum values |
| No SQL generation | Prompts explicitly forbid SQL; no DB connection in AI module |
| Account validation | Entity account codes verified against org's chart of accounts in Service layer |
| Confirmation gate | Mutating intents return `DRAFT` or require `confirm=true` flag |
| Temperature 0 | Deterministic extraction/classification calls |
| Audit trail | Log intent, entities, confidence, user_id, org_id |
| Grounding | Report queries fetch real DB data before NL formatting |

---

## 11. Multi-Tenant Isolation Strategy

**Model:** Shared database, shared schema, **`organization_id` on every tenant table**.

```mermaid
flowchart TB
    subgraph Request
        JWT[JWT: user_id, org_memberships]
        HDR[X-Org-Id header]
    end

    subgraph Middleware
        T1[TenantMiddleware]
        T2[Validate user belongs to org]
        T3[Set OrgContext on request.state]
    end

    subgraph Service
        S1[Every method accepts org_id]
    end

    subgraph Repository
        R1[BaseRepository.filter_by_org]
        R2[All queries include WHERE org_id = :org]
    end

    subgraph DB
        DB1[(MySQL — org_id column + indexes)]
    end

    JWT --> T1
    HDR --> T1
    T1 --> T2 --> T3 --> S1 --> R1 --> R2 --> DB1
```

### Isolation at Each Layer

| Layer | Mechanism |
|-------|-----------|
| **JWT** | Claims include allowed `org_ids`; no org in token alone — header required |
| **Middleware** | Rejects if `X-Org-Id` not in user's memberships |
| **Service** | `org_id` passed explicitly — never read from global state alone |
| **Repository** | `BaseRepository` enforces `org_id` filter on all SELECT/UPDATE/DELETE |
| **Database** | Composite indexes `(organization_id, id)`; optional FK constraints |
| **Storage** | Path prefix `{org_id}/{document_id}/` — no cross-org paths |
| **AI context** | Only org-scoped chart of accounts and summaries injected into prompts |

### Tenant-Scoped Tables (MVP)

- `organizations`, `organization_members`, `users`
- `documents`, `document_extractions`
- `ledger_accounts`, `journal_entries`, `journal_lines`
- `chat_sessions`, `chat_messages`, `audit_logs`

Global tables: none in MVP (system config via environment).

> **Optional (Production):** Row-Level Security policies, per-tenant encryption keys, dedicated schemas for enterprise tier.

---

## 12. Provider Abstractions

```mermaid
classDiagram
    class AIProvider {
        <<interface>>
        +complete_structured(messages, model) BaseModel
        +complete_text(messages) str
    }
    class OCRProvider {
        <<interface>>
        +extract_text(file_bytes) str
        +extract_with_layout(file_bytes) OCRResult
    }
    class StorageProvider {
        <<interface>>
        +save(org_id, key, data) str
        +read(path) bytes
        +delete(path) void
        +get_url(path) str
    }

    class GroqProvider {
        +complete_structured()
    }
    class TesseractProvider {
        +extract_text()
    }
    class LocalStorageProvider {
        +save()
    }

    AIProvider <|.. GroqProvider
    OCRProvider <|.. TesseractProvider
    StorageProvider <|.. LocalStorageProvider

    note for GroqProvider "MVP"
    note for TesseractProvider "MVP"
    note for LocalStorageProvider "MVP — swap to S3Provider"
```

Providers are registered in a simple DI container (`deps.py` or factory functions reading from `Settings`).

```python
# Settings-driven — conceptual
AI_PROVIDER=groq      # future: openai, azure
OCR_PROVIDER=tesseract  # future: textract, google_vision
STORAGE_PROVIDER=local    # future: s3
```

---

## 13. Background Processing Strategy

### MVP: FastAPI BackgroundTasks

```mermaid
flowchart LR
    REQ[API Request] --> SAVE[Save document + respond 201]
    SAVE --> BT[BackgroundTasks.add_task]
    BT --> PROC[process_document]
    PROC --> OCR & AI & DB
```

**Pros:** Zero extra infrastructure, simple to demo.  
**Cons:** Tasks lost on process restart; no retry queue; blocks same worker under heavy load.

### Migration Path → Celery + Redis

```mermaid
flowchart LR
    REQ[API Request] --> PUB[Celery delay]
    PUB --> REDIS[(Redis broker)]
    REDIS --> WRK[Celery worker]
    WRK --> PROC[Same process_document function]
```

| Phase | Trigger | Worker |
|-------|---------|--------|
| MVP | `BackgroundTasks` | Uvicorn process |
| v1.1 | Celery `.delay()` | Dedicated worker container |
| Prod | Celery + retry + dead-letter | Horizontal worker scaling |

The task function signature stays identical; only the **invocation mechanism** changes. Stub `tasks/celery_tasks.py` documents the future interface.

---

## 14. Data Model Overview

High-level ERD (implementation in Phase 3):

```mermaid
erDiagram
    ORGANIZATION ||--o{ ORGANIZATION_MEMBER : has
    USER ||--o{ ORGANIZATION_MEMBER : belongs
    ORGANIZATION ||--o{ LEDGER_ACCOUNT : owns
    ORGANIZATION ||--o{ JOURNAL_ENTRY : owns
    ORGANIZATION ||--o{ DOCUMENT : owns
    ORGANIZATION ||--o{ CHAT_SESSION : owns

    JOURNAL_ENTRY ||--|{ JOURNAL_LINE : contains
    JOURNAL_LINE }o--|| LEDGER_ACCOUNT : posts_to

    DOCUMENT ||--o| DOCUMENT_EXTRACTION : has
    DOCUMENT |o--o| JOURNAL_ENTRY : may_create

    CHAT_SESSION ||--o{ CHAT_MESSAGE : contains

    ORGANIZATION {
        uuid id PK
        string name
        string gstin
        string currency default INR
    }

    JOURNAL_ENTRY {
        uuid id PK
        uuid organization_id FK
        date entry_date
        string description
        enum status DRAFT POSTED VOID
        decimal total_amount
    }

    JOURNAL_LINE {
        uuid id PK
        uuid journal_entry_id FK
        uuid ledger_account_id FK
        decimal debit
        decimal credit
    }

    DOCUMENT {
        uuid id PK
        uuid organization_id FK
        string file_path
        enum status
        text ocr_text
        json extracted_data
    }
```

---

## 15. Security & RBAC

### Authentication

- **JWT access tokens** (short-lived, 15–30 min) + **refresh tokens** (stored hashed in DB)
- Passwords hashed with **bcrypt** via passlib
- Token payload: `sub` (user_id), no sensitive org data beyond membership list

### RBAC Roles (MVP)

| Role | Permissions |
|------|-------------|
| `OWNER` | All operations + org settings |
| `ACCOUNTANT` | Accounting write, document approve, reports |
| `VIEWER` | Read-only reports and documents |
| `ADMIN` | User management within org |

Permissions checked in `deps.require_permission("accounting:write")` — declarative on routers.

```mermaid
flowchart LR
    REQ[Request] --> AUTH[JWT valid?]
    AUTH --> ORG[User in org?]
    ORG --> RBAC[Role has permission?]
    RBAC --> HANDLER[Route handler]
```

---

## 16. Sync vs Async Database Strategy

| Concern | MVP Choice | Rationale |
|---------|------------|-----------|
| DB driver | **Sync SQLAlchemy + pymysql** | Simpler mental model; fewer async footguns for assignment |
| Route handlers | `async def` where awaiting AI/HTTP; sync `def` for DB-heavy | FastAPI runs sync DB in threadpool automatically |
| AI calls | **async** via httpx | Groq API is I/O bound |
| OCR | **sync** in BackgroundTask | Tesseract is CPU/subprocess — not on request path |
| Future | SQLAlchemy async + aiomysql | When concurrent DB load justifies complexity |

**Interview answer:** "We use async for I/O-bound external calls (LLM) and sync SQLAlchemy for MVP because our DB access pattern is straightforward request/response. BackgroundTasks keep OCR off the hot path. We can migrate to async sessions without changing Service/Repository interfaces."

---

## 17. Future Module Extraction Path

The modular monolith is designed for **evolutionary extraction**:

```mermaid
flowchart TB
    subgraph Now["MVP Modular Monolith"]
        M1[document_processing/]
        M2[ai/]
        M3[domain/accounting/]
        M4[services/]
    end

    subgraph Later["Extractable Services"]
        S1[Document Service]
        S2[AI Gateway]
        S3[Accounting Core]
    end

    M1 -->|HTTP/gRPC| S1
    M2 -->|HTTP/gRPC| S2
    M3 & M4 -->|event bus| S3
```

| Module | Extraction Trigger | Interface Already Defined |
|--------|-------------------|---------------------------|
| `document_processing/` | OCR queue backlog | `StorageProvider`, `OCRProvider` |
| `ai/` | Multi-model routing, rate limits | `AIProvider` |
| `domain/accounting/` | Regulatory audit requiring isolated ledger | Pure domain — no framework deps |
| `tasks/` | Need durable retries | Shared task function signatures |

**Rule:** Cross-module calls go through **Service interfaces**, never direct repository imports across bounded contexts.

---

## 18. Architectural Decision Records (ADRs)

### ADR-001: Modular Monolith over Microservices

**Status:** Accepted

**Context:** Solo/small-team MVP for an assignment; multiple domains (docs, AI, accounting) but tight integration.

**Decision:** Single deployable FastAPI app with strict module boundaries.

**Rationale:**
- Accounting entries and document approval are **strongly consistent** — same transaction boundary.
- Microservices add network latency, distributed tracing, and saga complexity inappropriate for MVP.
- Module folders mirror future service boundaries.

**Consequences:** Scale vertically first; extract hot modules when metrics demand it (see §17).

---

### ADR-002: Clean Architecture with Repository + Service Pattern

**Status:** Accepted

**Context:** Need testable business logic; frontend engineer learning backend patterns.

**Decision:** Routers → Services → Repositories → Domain; Domain has no framework imports.

**Rationale:**
- **Services** express use cases ("approve document and create draft entry") — readable in interviews.
- **Repositories** isolate SQLAlchemy — swap to raw SQL or different DB without touching services.
- **Domain** holds double-entry rules — unit test without DB.
- Matches FastAPI community best practices without heavy DDD ceremony.

**Consequences:** More files than "fat controllers"; pays off in testability and AI-safety boundaries.

---

### ADR-003: Intent-Based Chat (Not LLM-as-SQL)

**Status:** Accepted

**Context:** Users want natural language; LLMs hallucinate SQL and account codes.

**Decision:** LLM classifies intent + extracts entities → deterministic Python router → existing Service methods.

**Rationale:**
- Same validation path as REST API — no special "chat bypass."
- Unknown intents fail safe with clarification.
- Auditors can trace: intent → service method → DB row.

**Consequences:** Must maintain intent enum and router; new capabilities = new intent + service wiring (not prompt-only).

---

### ADR-004: Shared-Schema Multi-Tenancy

**Status:** Accepted

**Context:** B2B SaaS with many small Indian businesses; cost-sensitive MVP.

**Decision:** `organization_id` column on all tenant tables; enforced in repository base class.

**Rationale:**
- Simplest ops (one MySQL instance, one migration path).
- Alembic migrations apply once.
- Sufficient for assignment; enterprise can upgrade to schema-per-tenant later.

**Consequences:** Requires discipline — every query must filter by org; code review + repository base class mitigates.

---

### ADR-005: Provider Abstractions for AI, OCR, Storage

**Status:** Accepted

**Context:** MVP uses Groq + Tesseract + local disk; production likely differs.

**Decision:** ABC interfaces in `ai/providers`, `document_processing/ocr`, `document_processing/storage`.

**Rationale:**
- Environment-variable swap without code changes.
- Unit tests use fake providers.
- Demonstrates **Dependency Inversion Principle** in interviews.

**Consequences:** One extra indirection layer — acceptable for three external systems.

---

### ADR-006: Decimal for All Monetary Values

**Status:** Accepted

**Context:** Float rounding errors are unacceptable in accounting (₹0.01 breaks reconciliation).

**Decision:** Python `decimal.Decimal`; MySQL `DECIMAL(19,4)`; Pydantic `condecimal`; JSON as string if needed.

**Rationale:** Industry standard for financial software; GST calculations require exact arithmetic.

**Consequences:** Slightly verbose serialization; never use native JSON number for money in API docs.

---

### ADR-007: FastAPI BackgroundTasks for MVP Async Work

**Status:** Accepted

**Context:** Document OCR + AI extraction takes 5–30 seconds; cannot block upload response.

**Decision:** `BackgroundTasks` for `process_document`; document Celery migration in `tasks/celery_tasks.py`.

**Rationale:**
- No Redis/RabbitMQ dependency for demo/deploy.
- Task logic written once, invoked differently later.

**Consequences:** No automatic retry on crash until Celery migration — acceptable for MVP with manual retry endpoint.

---

### ADR-008: JWT + RBAC (Not Session Cookies)

**Status:** Accepted

**Context:** Separate frontend SPA on different origin.

**Decision:** Stateless JWT access tokens; org context via `X-Org-Id` header; role permissions in deps.

**Rationale:**
- Standard SPA pattern; no server-side session store.
- Easy to document in OpenAPI.

**Consequences:** Token revocation requires blocklist or short TTL + refresh flow — implement refresh token rotation in Phase 3.

---

### ADR-009: India-First Compliance Module

**Status:** Accepted

**Context:** Phase 1 assumption — INR, GST (CGST/SGST/IGST), TDS.

**Decision:** `domain/compliance/gst.py` and `tds.py` as pure functions; extensible for other jurisdictions later.

**Rationale:**
- Keeps tax logic out of services and AI prompts.
- AI extracts GSTIN and tax amounts; **domain** validates rates and splits.

**Consequences:** International expansion requires new compliance modules — not hardcoded in accounting service.

---

### ADR-010: Sync SQLAlchemy for MVP

**Status:** Accepted

**Context:** Team learning curve; moderate expected concurrency for assignment demo.

**Decision:** Sync `Session` with pymysql; async routes only for external I/O.

**Rationale:** SQLAlchemy 2.x sync API is mature; async adds session lifecycle complexity without MVP benefit.

**Consequences:** Monitor connection pool; migrate to async if latency benchmarks require it.

---

## 19. Interview Defense Guide

### "Why modular monolith instead of microservices?"

> "Accounting requires ACID transactions across documents and journal entries. A monolith lets us commit uploads and entries in one database transaction without sagas. We've drawn module boundaries—document processing, AI, accounting domain—that map 1:1 to future services if load requires extraction. Microservices prematurely would slow development and complicate consistency for no scaling benefit yet."

### "Why repository + service instead of fat controllers?"

> "Routers handle HTTP; services handle use cases; repositories handle persistence. If GST rules change, I edit `domain/compliance/gst.py` and unit test it without spinning up FastAPI. If we switch from MySQL to Postgres, I change repositories—not 20 router files. It also enforces that AI never touches repositories directly."

### "Why intent-based chat instead of RAG-over-SQL?"

> "LLMs hallucinate SQL and account IDs. We use the LLM only to classify intent and extract entities into a Pydantic schema. A deterministic router calls the same `AccountingService` methods as our REST API. Mutations require confirmation. The LLM formats the final natural language response from real DB data—grounded, not invented."

### "How does tenant isolation work?"

> "Every layer participates: JWT proves identity, middleware validates org membership from `X-Org-Id`, services receive `org_id` explicitly, repositories inherit a base class that adds `WHERE organization_id = ?` to every query, and files are stored under `{org_id}/` prefixes. Defense in depth—no single layer is the sole gatekeeper."

### "How do you control AI hallucinations?"

> "Structured outputs validated by Pydantic, temperature zero for extraction, account codes verified against the org's chart of accounts, no SQL in prompts, mutating intents require confirmation, and report responses are formatted from actual query results—not LLM-generated numbers."

### "Sync or async for the database?"

> "Sync SQLAlchemy for MVP—simpler and sufficient for assignment scale. Async `httpx` for Groq calls. OCR runs in background tasks off the request path. FastAPI runs sync DB code in a thread pool. We can adopt async SQLAlchemy later without changing service interfaces."

### "How would you extract modules later?"

> "Each module already communicates through provider interfaces and service methods—not cross-repository imports. Document processing could become a standalone worker consuming upload events; AI could become a gateway service. Domain accounting is pure Python with no framework deps—it's the easiest to extract as a core ledger service."

---

## 20. Optional Production Enhancements

| Enhancement | Priority | Notes |
|-------------|----------|-------|
| Celery + Redis task queue | High | Durable document processing |
| S3 / MinIO storage | High | Replace local filesystem |
| AWS Textract / Google Vision OCR | Medium | Better accuracy than Tesseract |
| OpenAI / Azure fallback for AI | Medium | Multi-provider via `AIProvider` |
| Refresh token rotation + revocation | High | Security hardening |
| Rate limiting (slowapi) | Medium | Per org + per user |
| OpenTelemetry tracing | Medium | Cross-service prep |
| Materialized account balances | Medium | Avoid SUM on every report |
| Period locking | High | Prevent backdated edits |
| Webhook notifications | Low | Document processed events |
| Read replicas | Low | Report query offload |
| Schema-per-tenant (enterprise) | Low | Stronger isolation |
| Automated test suite (>80% domain coverage) | High | Before production |
| CI/CD pipeline | High | Lint, test, migrate, deploy |

---

## Appendix A: API Surface (Preview for Phase 3)

| Method | Path | Module |
|--------|------|--------|
| POST | `/api/v1/auth/register` | auth |
| POST | `/api/v1/auth/login` | auth |
| POST | `/api/v1/auth/refresh` | auth |
| GET | `/api/v1/organizations/me` | organizations |
| POST | `/api/v1/documents/upload` | documents |
| GET | `/api/v1/documents/{id}` | documents |
| PATCH | `/api/v1/documents/{id}/extraction` | documents |
| POST | `/api/v1/documents/{id}/approve` | documents |
| GET | `/api/v1/accounting/accounts` | accounting |
| POST | `/api/v1/accounting/journal-entries` | accounting |
| GET | `/api/v1/accounting/journal-entries` | accounting |
| POST | `/api/v1/chat/sessions` | chat |
| POST | `/api/v1/chat/sessions/{id}/messages` | chat |
| GET | `/api/v1/reports/trial-balance` | reports |
| GET | `/api/v1/reports/expenses` | reports |
| GET | `/health` | health |

---

## Appendix B: Configuration (Environment Variables Preview)

```env
# App
APP_ENV=development
SECRET_KEY=
DATABASE_URL=mysql+pymysql://user:pass@localhost:3306/ai_accounting

# Providers
AI_PROVIDER=groq
GROQ_API_KEY=
OCR_PROVIDER=tesseract
STORAGE_PROVIDER=local
STORAGE_LOCAL_PATH=./data/uploads

# Auth
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# CORS
CORS_ORIGINS=http://localhost:5173
```

---

*End of Phase 2 System Design — ready for Phase 3 implementation.*
