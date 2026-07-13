from __future__ import annotations

import json
from datetime import datetime, timezone
from decimal import Decimal
from sqlalchemy.orm import Session

from app.core.exceptions import ResourceNotFoundError, ValidationError
from app.models.chat import ChatSession, ChatMessage
from app.models.document import Document
from app.models.account import Account
from app.schemas.chat import ChatSessionOut, ChatMessageOut, ChatQueryResponse
from app.ai.groq_provider import GroqProvider
from app.services.report_service import ReportService
from app.services.accounting_service import AccountingService
from app.schemas.accounting import JournalEntryCreate
from app.models.invoice import Invoice
from app.models.expense import Expense
from app.services.invoice_service import InvoiceService
from app.services.reconciliation_service import ReconciliationService
from app.models.reconciliation import BankAccount



class ChatService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.ai = GroqProvider()

    def create_session(self, organization_id: int) -> ChatSessionOut:
        session = ChatSession(
            organization_id=organization_id,
            created_at=datetime.now(timezone.utc).isoformat(),
        )
        self.db.add(session)
        self.db.commit()
        self.db.refresh(session)
        return ChatSessionOut.model_validate(session)

    def list_sessions(self, organization_id: int) -> list[ChatSessionOut]:
        sessions = self.db.query(ChatSession).filter(ChatSession.organization_id == organization_id).order_by(ChatSession.id.desc()).all()
        return [ChatSessionOut.model_validate(s) for s in sessions]

    def get_messages(self, session_id: int, organization_id: int) -> list[ChatMessageOut]:
        # Validate session
        session = self.db.query(ChatSession).filter(ChatSession.id == session_id, ChatSession.organization_id == organization_id).first()
        if not session:
            raise ResourceNotFoundError(f"Chat session {session_id} not found")

        messages = self.db.query(ChatMessage).filter(ChatMessage.session_id == session_id).order_by(ChatMessage.id.asc()).all()
        return [ChatMessageOut.model_validate(m) for m in messages]

    def handle_message(self, session_id: int, organization_id: int, content: str) -> ChatQueryResponse:
        session = self.db.query(ChatSession).filter(ChatSession.id == session_id, ChatSession.organization_id == organization_id).first()
        if not session:
            raise ResourceNotFoundError(f"Chat session {session_id} not found")

        # 1. Save user message
        user_message = ChatMessage(
            session_id=session_id,
            sender="user",
            content=content,
            created_at=datetime.now(timezone.utc).isoformat(),
        )
        self.db.add(user_message)
        self.db.commit()
        self.db.refresh(user_message)

        # 2. Classify intent
        classification = self.ai.classify_intent(content)
        intent = classification.get("intent", "UNKNOWN")
        confidence = classification.get("confidence", 0.0)
        entities = classification.get("entities", {})

        # Update user message with classified intent
        user_message.intent = intent
        self.db.add(user_message)
        self.db.commit()

        # 3. Retrieve database context depending on intent
        db_context = {}
        report_svc = ReportService(self.db)

        if intent == "QUERY_BALANCE":
            try:
                db_context["trial_balance"] = report_svc.get_trial_balance(organization_id)
            except Exception as exc:
                db_context["error"] = f"Failed to load trial balance: {exc}"

        elif intent == "QUERY_EXPENSES":
            try:
                db_context["expenses_summary"] = report_svc.get_expenses_summary(organization_id)
            except Exception as exc:
                db_context["error"] = f"Failed to load expenses: {exc}"

        elif intent == "QUERY_INVOICES":
            try:
                invoices = self.db.query(Invoice).filter(Invoice.organization_id == organization_id).order_by(Invoice.id.desc()).all()
                db_context["invoices"] = [
                    {
                        "id": inv.id,
                        "invoice_number": inv.invoice_number,
                        "customer_name": inv.customer_name,
                        "total": str(inv.total),
                        "status": inv.status,
                        "due_date": inv.due_date,
                    }
                    for inv in invoices
                ]
            except Exception as exc:
                db_context["error"] = f"Failed to load invoices: {exc}"

        elif intent == "PAY_INVOICE":
            invoice_id = entities.get("invoice_id")
            if invoice_id:
                try:
                    invoice = InvoiceService(self.db).pay(int(invoice_id), organization_id)
                    db_context["result"] = f"Invoice {invoice.invoice_number} successfully marked as paid and payment recorded in ledger."
                    db_context["invoice"] = {
                        "id": invoice.id,
                        "invoice_number": invoice.invoice_number,
                        "status": invoice.status,
                        "total": str(invoice.total),
                    }
                except Exception as exc:
                    db_context["error"] = f"Failed to mark invoice as paid: {exc}"
            else:
                db_context["error"] = "No invoice ID was provided. Please say 'Mark invoice #123 as paid'."

        elif intent == "RECONCILE":
            tx_id = entities.get("transaction_id")
            je_id = entities.get("journal_entry_id")
            recon_svc = ReconciliationService(self.db)
            if tx_id and je_id:
                try:
                    tx = recon_svc.manual_match(organization_id, int(tx_id), int(je_id))
                    db_context["result"] = f"Successfully matched bank transaction #{tx.id} with ledger journal entry #{je_id}."
                except Exception as exc:
                    db_context["error"] = f"Failed to manually reconcile: {exc}"
            else:
                try:
                    bank_acc = self.db.query(BankAccount).filter(BankAccount.organization_id == organization_id).first()
                    if not bank_acc:
                        from app.schemas.reconciliation import BankAccountCreate
                        bank_acc = recon_svc.create_bank_account(organization_id, BankAccountCreate(name="Default Bank Account", account_number="123456789"))

                    matched_count = recon_svc.auto_reconcile(organization_id, bank_acc.id)
                    db_context["result"] = f"Auto-reconciled bank transactions for account '{bank_acc.name}'. Reconciled: {matched_count} matching entries."
                except Exception as exc:
                    db_context["error"] = f"Failed to perform auto reconciliation: {exc}"

        elif intent == "SEARCH_DOCUMENTS":
            try:
                docs = self.db.query(Document).filter(Document.organization_id == organization_id).order_by(Document.id.desc()).limit(10).all()
                db_context["recent_documents"] = [
                    {
                        "id": d.id,
                        "document_type": d.document_type,
                        "filename": d.filename,
                        "status": d.status,
                        "description": d.description,
                        "extracted_data": d.extracted_data,
                    }
                    for d in docs
                ]
            except Exception as exc:
                db_context["error"] = f"Failed to search documents: {exc}"

        elif intent == "CREATE_ENTRY":
            # Formulate proposal
            amt = entities.get("amount") or entities.get("total") or "0.00"
            desc = entities.get("description") or entities.get("vendor") or "Expense entry"
            db_context["proposed_entry"] = {
                "description": desc,
                "amount": str(amt),
                "required_accounts": ["5000 (Expense)", "1100 (Cash)"],
                "instructions": "To post this entry, type 'Confirm posting ₹5000' or call the /ledger/journal-entries API.",
            }

        else:
            db_context["info"] = "No specific database query was triggered for this intent."

        # 4. Generate final assistant message formatted by Groq
        prompt = (
            f"You are a friendly, concise, and professional accounting AI assistant.\n"
            f"User message: '{content}'\n"
            f"Classified intent: {intent} (confidence: {confidence})\n"
            f"Database retrieved context: {json.dumps(db_context)}\n\n"
            f"Formulate a helpful response in markdown. Explain any numbers in a friendly manner. "
            f"Do not invent data outside the context."
        )

        response_text = self.ai.generate_response(prompt)

        # 5. Save assistant message
        assistant_message = ChatMessage(
            session_id=session_id,
            sender="assistant",
            content=response_text,
            created_at=datetime.now(timezone.utc).isoformat(),
        )
        self.db.add(assistant_message)
        self.db.commit()

        return ChatQueryResponse(
            session_id=session_id,
            response=response_text,
            intent=intent,
            confidence=confidence,
            entities=entities,
        )
