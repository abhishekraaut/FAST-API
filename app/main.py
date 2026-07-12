from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.routers.accounting import router as accounting_router
from app.api.v1.routers.accounts import router as accounts_router
from app.api.v1.routers.auth import router as auth_router
from app.api.v1.routers.clients import router as clients_router
from app.api.v1.routers.documents import router as documents_router
from app.api.v1.routers.expenses import router as expenses_router
from app.api.v1.routers.health import router as health_router
from app.api.v1.routers.invoices import router as invoices_router
from app.api.v1.routers.ledger import router as ledger_router
from app.api.v1.routers.organizations import router as organizations_router
from app.api.v1.routers.vendors import router as vendors_router
from app.database.session import init_db

app = FastAPI(title="AI Accounting API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router)
app.include_router(auth_router)
app.include_router(organizations_router)
app.include_router(clients_router)
app.include_router(vendors_router)
app.include_router(documents_router)
app.include_router(accounts_router)
app.include_router(ledger_router)
app.include_router(accounting_router)
app.include_router(invoices_router)
app.include_router(expenses_router)


@app.on_event("startup")
def startup() -> None:
    init_db()
