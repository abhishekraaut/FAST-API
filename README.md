# AI Accounting & Document Ingestion System

An enterprise-grade, multi-tenant AI-powered accounting and bookkeeping platform. This backend system enables automated financial document ingestion, OCR parsing, AI structured data extraction, double-entry ledger bookkeeping, payment tracking, bank reconciliation, financial reports generation, and conversational chat-based accounting actions.

---

## Key Features
- **Tenancy-Scoped Ledger**: Fully isolated double-entry bookkeeping ledgers scoped by organization ID.
- **OCR & LLM Document Extraction**: Asynchronous invoice/receipt extraction integrating Tesseract CLI and Groq LLM API.
- **Auto-Posting & Payment Tracking**: Invoices and expenses can be created, approved, paid, and posted automatically to ledger accounts.
- **Bank Reconciliation Engine**: Automatic matching of bank statements with ledger journal entries based on date and amount, alongside manual match overrides.
- **Reports Engine**: Generates real-time Trial Balance, Profit & Loss, GST/TDS tax liabilities, and vendor expenses summaries.
- **Conversational Chat Assistant**: An intent-based conversational agent that processes queries and fires ledger actions directly from natural language prompts.

---

## System Requirements & Prerequisites
- **Python**: Version `3.10` or higher (Fully compatible with Python `3.13` and `3.14`).
- **PostgreSQL**: Version `12` or higher (Ensure you have a running PostgreSQL instance and have created a database).
- **Groq API Key**: Optional but recommended for full AI features (If not provided, the system gracefully uses robust regex & keyword offline extraction/intent fallbacks).
- **Tesseract OCR**: Optional but recommended for physical image OCR capabilities.

---

## Quick Setup & Installation

Follow these simple steps to set up and launch the application locally:

### 1. Clone & Navigate to the Project Root
```bash
cd "3rd Technical assignment/FAST API"
```

### 2. Set Up a Virtual Environment
**Windows:**
```bash
python -m venv .venv
.venv\Scripts\activate
```
**macOS/Linux:**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables
Create a file named `.env` in the root directory and add the following keys:
```env
# Server Configurations
HOST=127.0.0.1
PORT=8000
DATABASE_URL=postgresql://postgres:password@localhost:5432/accounting_db

# LLM Configurations
AI_API_KEY=your-groq-api-key-here
AI_MODEL=llama3-8b-8192


# JWT Security
SECRET_KEY=your-jwt-signing-secret-key-here
ACCESS_TOKEN_EXPIRE_MINUTES=60
```

---

## Running the Application

Start the FastAPI development server:
```bash
uvicorn app.main:app --reload
```

Once running, the application will be hosted at: `http://127.0.0.1:8000`

---

## Testing & API Documentation

### 1. Interactive API Docs (Swagger UI)
FastAPI generates interactive API documentation automatically. While the server is running, navigate to:
- **Swagger UI**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs) (Highly recommended for testing endpoints manually).
- **Redoc Docs**: [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)

### 2. Testing with Postman
To perform manual API testing in Postman:
1. Create a new collection in Postman.
2. Define `X-Org-Id` in the headers (e.g. `X-Org-Id: 1`) to scope requests to the correct organization context.
3. Import or trigger the following sample routes:
   - **Auth (Register/Login)**: `POST /auth/register` & `POST /auth/login`
   - **Upload Invoice/Receipt**: `POST /documents/upload` (Form-data payload: `file: [PDF/Image]`)
   - **Chat Assistant**: `POST /chat/sessions/{session_id}/messages?organization_id=1` (JSON payload: `{"content": "Show unpaid invoices"}`)
   - **Generate P&L Report**: `GET /reports/profit-loss?organization_id=1`
   - **Auto Reconcile Bank Statements**: `POST /reconciliation/bank-accounts/1/auto-reconcile?organization_id=1`

---

## Running Automated Unit Tests

Run the complete test suite locally to verify code correctness and compatibility:
```bash
python -m pytest
```

You should see all unit tests compile and pass successfully:
```bash
======================= 21 passed, 3 warnings in 2.48s ========================
```
