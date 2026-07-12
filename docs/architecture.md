# AI Accounting & Document Management System

## 1. System Architecture

This project is designed as a production-style SaaS foundation for an AI-powered accounting workspace. The frontend is a React 19 + TypeScript application built around a feature-based structure, while the backend is a modular FastAPI service following clean architecture principles.

### Backend architecture
- FastAPI provides a high-performance REST API layer.
- The application is split into API, service, repository, schema, and model layers.
- Business logic is kept out of routes and pushed into service classes.
- SQLAlchemy 2.0 models and Pydantic v2 schemas provide a typed persistence boundary.
- AI and OCR capabilities are abstracted behind interfaces so OpenAI/Groq can be swapped out without altering business workflow.

### Why this structure works
- Separation of concerns makes onboarding easier for a transitioning full-stack developer.
- Feature modules can grow independently without causing coupling.
- The app can support multi-tenant expansion later with company-scoped data access.

## 2. Folder Structure

### Frontend
src/
  app/
  components/
  features/
    auth/
    dashboard/
    documents/
    invoices/
    expenses/
    ledger/
    reports/
    chat/
    tasks/
  hooks/
  layouts/
  pages/
  services/
  api/
  types/
  utils/
  constants/
  routes/
  store/
  theme/

### Backend
app/
  api/
    v1/
      routers/
  core/
  config/
  database/
  models/
  schemas/
  repositories/
  services/
  ai/
  ocr/
  accounting/
  middleware/
  utils/

## 3. Database ER Diagram

Users 1---* Companies
Companies 1---* Clients
Companies 1---* Documents
Companies 1---* Invoices
Companies 1---* Expenses
Companies 1---* LedgerEntries
Companies 1---* Payments
Companies 1---* TaxRecords
Companies 1---* Tasks
Companies 1---* Reminders
Companies 1---* ChatHistory
Companies 1---* AISessions
Companies 1---* Reports
Companies 1---* AuditLogs

Invoices 1---* InvoiceItems
Payments *---1 Invoices
Expenses *---1 Categories

## 4. API Design

### Auth
- POST /api/auth/register
- POST /api/auth/login
- POST /api/auth/refresh
- GET /api/auth/me

### Core modules
- GET /api/documents
- POST /api/documents/upload
- GET /api/invoices
- POST /api/invoices
- GET /api/expenses
- POST /api/expenses
- GET /api/ledger
- GET /api/reports
- POST /api/chat/query
- GET /api/tasks

## 5. UI Wireframes

- Landing page with hero, feature cards, and CTA.
- Auth experience with split-screen marketing panel.
- Dashboard with metric cards, charts, tables, and AI assistant panel.
- Document workspace with drag-and-drop upload and status list.
- Invoice and expense management screens with filter/search/pagination.

## 6. Development Roadmap

1. Set up monorepo-style folder structure and core styling.
2. Implement authentication, layout, and dashboard shell.
3. Build document upload and OCR workflow UI.
4. Add invoice, expense, and ledger modules.
5. Add reports, reminders, and chat assistant.
6. Connect backend APIs and polish the experience.
